"""Small Streamlit dashboard for customer segmentation and product recommendations."""
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.pipeline import clean_retail_data, calculate_rfm, cluster_customers, generate_cluster_recommendations, recommend_for_customer

st.set_page_config(page_title="Retail Customer Segmentation", page_icon="🛍️", layout="wide")
st.title("Retail Customer Segmentation & Product Recommendations")
st.write("Upload an Online Retail CSV or Excel file to calculate RFM metrics, segment customers, and explore cluster-level product recommendations.")
uploaded = st.file_uploader("Upload retail transactions", type=["csv", "xlsx", "xls"])
clusters = st.sidebar.slider("Number of customer clusters", min_value=2, max_value=8, value=5)
top_n = st.sidebar.slider("Products per cluster", min_value=3, max_value=20, value=10)

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith((".xlsx", ".xls")):
            raw = pd.read_excel(uploaded)
        else:
            raw = pd.read_csv(uploaded, encoding_errors="replace")
        st.subheader("Raw data preview")
        st.dataframe(raw.head(10), use_container_width=True)
        clean = clean_retail_data(raw)
        rfm = calculate_rfm(clean)
        segmented, _, _ = cluster_customers(rfm, n_clusters=clusters)
        recs = generate_cluster_recommendations(clean, segmented, top_n=top_n, min_customer_count=1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Valid sales rows", f"{len(clean):,}")
        c2.metric("Customers", f"{len(segmented):,}")
        c3.metric("Clusters", int(segmented["Cluster"].nunique()))

        st.subheader("Customer segments")
        st.dataframe(segmented.sort_values(["Cluster", "Monetary"], ascending=[True, False]), use_container_width=True)
        profile = segmented.groupby("Cluster").agg(
            Customers=("CustomerID", "nunique"),
            Median_Recency=("Recency", "median"),
            Median_Frequency=("Frequency", "median"),
            Median_Monetary=("Monetary", "median"),
        ).reset_index()
        st.subheader("Cluster profile")
        st.dataframe(profile, use_container_width=True)
        st.bar_chart(profile.set_index("Cluster")[["Customers"]])

        st.subheader("Product recommendations by cluster")
        st.dataframe(recs, use_container_width=True)

        customer_ids = segmented["CustomerID"].astype(str).sort_values().unique().tolist()
        selected = st.selectbox("Choose a customer", customer_ids)
        customer_recs = recommend_for_customer(selected, segmented, recs, transactions=clean, top_n=5)
        st.write("Recommended products not already present in the customer's purchase history:")
        st.dataframe(customer_recs, use_container_width=True)

        st.subheader("Download results")
        st.download_button("Download customer segments CSV", segmented.to_csv(index=False), "customer_segments.csv", "text/csv")
        st.download_button("Download recommendations CSV", recs.to_csv(index=False), "cluster_product_recommendations.csv", "text/csv")
    except Exception as exc:
        st.error(f"Could not process this file: {exc}")
        st.info("Check that the file includes InvoiceNo, Description, Quantity, InvoiceDate, UnitPrice, and CustomerID columns.")
else:
    st.info("Upload a retail transaction file to begin. The dataset is not bundled with this repository; see README.md for instructions.")
    st.markdown("**Expected columns:** `InvoiceNo`, `StockCode` (optional), `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country` (optional).")
