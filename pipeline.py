"""Customer segmentation and cluster-based product recommendations.

Expected input columns follow the UCI Online Retail dataset:
InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.
"""
from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


REQUIRED_COLUMNS = {
    "InvoiceNo", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"
}


def load_retail_data(path: str) -> pd.DataFrame:
    """Load a CSV or Excel retail transaction file."""
    lower = path.lower()
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    if lower.endswith(".csv"):
        return pd.read_csv(path, encoding_errors="replace")
    raise ValueError("Supported input formats are .csv, .xlsx, and .xls")


def clean_retail_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns and remove records unsuitable for customer-level RFM.

    Missing customer IDs are excluded rather than imputed. Non-positive quantities
    are excluded from the recommendation/positive-sales analysis because they may
    represent returns or corrections; retain the raw file for separate returns analysis.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    data = df.copy()
    data.columns = [str(c).strip() for c in data.columns]
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    for col in ["Quantity", "UnitPrice"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["CustomerID"] = data["CustomerID"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    data["Description"] = data["Description"].astype("string").str.strip()
    data["InvoiceNo"] = data["InvoiceNo"].astype("string").str.strip()

    data = data.dropna(subset=["CustomerID", "Description", "InvoiceDate", "Quantity", "UnitPrice"])
    data = data[
        data["CustomerID"].ne("")
        & data["Description"].ne("")
        & data["InvoiceNo"].ne("")
        & (data["Quantity"] > 0)
        & (data["UnitPrice"] > 0)
    ].copy()
    data["Revenue"] = (data["Quantity"] * data["UnitPrice"]).round(2)
    if data.empty:
        raise ValueError("No valid sales rows remain after cleaning.")
    return data


def calculate_rfm(data: pd.DataFrame, reference_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """Calculate customer Recency (days), Frequency (unique invoices), and Monetary."""
    required = {"CustomerID", "InvoiceNo", "InvoiceDate", "Revenue"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Data must contain columns: {', '.join(sorted(missing))}")
    if data.empty:
        raise ValueError("Cannot calculate RFM from an empty dataframe.")
    if reference_date is None:
        reference_date = pd.to_datetime(data["InvoiceDate"]).max().normalize() + pd.Timedelta(days=1)
    else:
        reference_date = pd.Timestamp(reference_date)
        if reference_date.tz is not None:
            reference_date = reference_date.tz_localize(None)
    rfm = data.groupby("CustomerID", as_index=False).agg(
        LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Revenue", "sum"),
    )
    rfm["Recency"] = (reference_date.normalize() - pd.to_datetime(rfm["LastPurchase"]).dt.normalize()).dt.days
    rfm["Monetary"] = rfm["Monetary"].round(2)
    rfm = rfm[["CustomerID", "Recency", "Frequency", "Monetary"]]
    return rfm.sort_values("CustomerID").reset_index(drop=True)


def cluster_customers(rfm: pd.DataFrame, n_clusters: int = 5, random_state: int = 42) -> tuple[pd.DataFrame, KMeans, StandardScaler]:
    """Cluster customers on scaled log-transformed RFM metrics.

    Returns a copy of RFM with a Cluster column, fitted KMeans model and scaler.
    """
    features = ["Recency", "Frequency", "Monetary"]
    missing = set(features + ["CustomerID"]).difference(rfm.columns)
    if missing:
        raise ValueError(f"RFM data is missing columns: {', '.join(sorted(missing))}")
    if rfm.empty:
        raise ValueError("Cannot cluster an empty RFM dataframe.")
    n_clusters = int(n_clusters)
    if n_clusters < 1:
        raise ValueError("n_clusters must be at least 1.")
    n_clusters = min(n_clusters, len(rfm))
    X = rfm[features].astype(float).copy()
    # RFM is non-negative by definition; clipping avoids invalid log transforms.
    X = np.log1p(X.clip(lower=0))
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    result = rfm.copy()
    result["Cluster"] = model.fit_predict(X_scaled)
    return result, model, scaler


def generate_cluster_recommendations(
    transactions: pd.DataFrame,
    segmented_rfm: pd.DataFrame,
    top_n: int = 10,
    min_customer_count: int = 2,
) -> pd.DataFrame:
    """Recommend frequently purchased products within each customer cluster.

    Ranking is based on distinct customers in a cluster who purchased each product,
    with units sold as a tie-breaker. This is a transparent baseline, not a learned
    semantic recommender. The transaction frame should be the cleaned positive-sales
    data and segmented_rfm must contain CustomerID and Cluster.
    """
    needed_tx = {"CustomerID", "Description", "Quantity"}
    needed_seg = {"CustomerID", "Cluster"}
    if not needed_tx.issubset(transactions.columns):
        raise ValueError(f"transactions must contain {', '.join(sorted(needed_tx))}")
    if not needed_seg.issubset(segmented_rfm.columns):
        raise ValueError("segmented_rfm must contain CustomerID and Cluster")
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    joined = transactions.merge(segmented_rfm[["CustomerID", "Cluster"]], on="CustomerID", how="inner")
    if joined.empty:
        return pd.DataFrame(columns=["Cluster", "Description", "CustomerCount", "UnitsSold", "Rank"])
    recs = joined.groupby(["Cluster", "Description"], as_index=False).agg(
        CustomerCount=("CustomerID", "nunique"),
        UnitsSold=("Quantity", "sum"),
    )
    recs = recs[recs["CustomerCount"] >= int(min_customer_count)].copy()
    recs = recs.sort_values(
        ["Cluster", "CustomerCount", "UnitsSold", "Description"],
        ascending=[True, False, False, True],
    )
    recs["Rank"] = recs.groupby("Cluster").cumcount() + 1
    return recs[recs["Rank"] <= top_n].reset_index(drop=True)


def recommend_for_customer(
    customer_id: str,
    segmented_rfm: pd.DataFrame,
    cluster_recommendations: pd.DataFrame,
    transactions: Optional[pd.DataFrame] = None,
    top_n: int = 5,
) -> pd.DataFrame:
    """Return cluster-level products not already purchased by a customer, if history supplied."""
    matches = segmented_rfm[segmented_rfm["CustomerID"].astype(str) == str(customer_id)]
    if matches.empty:
        raise KeyError(f"Customer {customer_id!r} was not found in the RFM table.")
    cluster = matches.iloc[0]["Cluster"]
    candidates = cluster_recommendations[cluster_recommendations["Cluster"] == cluster].copy()
    if transactions is not None and not candidates.empty:
        purchased = set(
            transactions.loc[transactions["CustomerID"].astype(str) == str(customer_id), "Description"]
            .astype(str)
            .tolist()
        )
        candidates = candidates[~candidates["Description"].astype(str).isin(purchased)]
    return candidates.head(top_n).reset_index(drop=True)
