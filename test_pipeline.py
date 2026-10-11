import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pipeline import clean_retail_data, calculate_rfm, cluster_customers, generate_cluster_recommendations, recommend_for_customer


@pytest.fixture
def transactions():
    return pd.DataFrame({
        "InvoiceNo": ["100", "100", "101", "102", "102", "103", "104", "105"],
        "Description": ["Mug", "Tea", "Mug", "Tea", "Plate", "Plate", "Mug", "Tea"],
        "Quantity": [2, 1, 1, 3, 1, 2, 4, 1],
        "InvoiceDate": ["2022-01-01", "2022-01-01", "2022-01-10", "2022-01-11", "2022-01-11", "2022-01-15", "2022-01-20", "2022-01-25"],
        "UnitPrice": [3, 2, 3, 2, 5, 5, 3, 2],
        "CustomerID": ["A", "A", "A", "B", "B", "C", "C", "D"],
        "Country": ["UK"] * 8,
    })


def test_clean_drops_invalid_rows_and_calculates_revenue(transactions):
    transactions.loc[len(transactions)] = ["106", "Bad", -2, "2022-01-26", 2, "D", "UK"]
    clean = clean_retail_data(transactions)
    assert (clean["Quantity"] > 0).all()
    assert (clean["UnitPrice"] > 0).all()
    assert "Revenue" in clean.columns
    assert not clean["CustomerID"].isna().any()


def test_rfm_values_are_correct(transactions):
    clean = clean_retail_data(transactions)
    rfm = calculate_rfm(clean, reference_date=pd.Timestamp("2022-01-26"))
    a = rfm.set_index("CustomerID").loc["A"]
    assert a["Frequency"] == 2
    assert a["Monetary"] == 11.0
    assert a["Recency"] == 16


def test_clustering_and_recommendations(transactions):
    clean = clean_retail_data(transactions)
    rfm = calculate_rfm(clean)
    segmented, model, scaler = cluster_customers(rfm, n_clusters=2)
    assert "Cluster" in segmented.columns
    assert segmented["Cluster"].nunique() <= 2
    recs = generate_cluster_recommendations(clean, segmented, top_n=3, min_customer_count=1)
    assert set(["Cluster", "Description", "CustomerCount", "UnitsSold", "Rank"]).issubset(recs.columns)
    customer = str(segmented.iloc[0]["CustomerID"])
    result = recommend_for_customer(customer, segmented, recs, transactions=clean, top_n=2)
    assert len(result) <= 2


def test_missing_required_columns_raise():
    with pytest.raises(ValueError, match="Missing required columns"):
        clean_retail_data(pd.DataFrame({"foo": [1]}))
