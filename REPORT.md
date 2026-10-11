# Project Report: Retail Customer Segmentation & Product Recommendations

**Author:** Touseeq Danish

## Abstract
This project studies customer behavior in retail transaction data using exploratory data analysis, Recency-Frequency-Monetary (RFM) metrics, K-Means clustering, and a simple cluster-based product recommendation baseline. The code is designed around the Online Retail dataset and includes a reusable pipeline, notebook, dashboard, and tests.

## 1. Problem statement
Retailers can use transaction histories to better understand customer engagement and purchasing value. The project aims to group customers with similar transaction patterns and surface products that are popular among customers in the same group.

## 2. Dataset
The project expects the UCI Online Retail dataset, which contains transaction-level records such as invoice identifiers, product descriptions, quantities, invoice dates, unit prices, customer identifiers, and country. The data file is not included in the repository and must be downloaded separately. This report therefore does not claim dataset row counts or computed statistics.

## 3. Data preparation
The pipeline standardizes column names and parses invoice dates and numeric fields. Records without a customer ID, product description, invoice identifier, valid date, positive quantity, or positive unit price are excluded from the positive-sales analysis. Customer IDs are not imputed because a missing identifier cannot reliably be reconstructed. Returns and cancellations should be investigated separately if they are important to the use case.

## 4. RFM features
The pipeline computes the following customer-level features:

- **Recency:** days from the customer's latest purchase to one day after the latest transaction date in the dataset.
- **Frequency:** number of unique invoices associated with the customer.
- **Monetary:** total revenue calculated as quantity multiplied by unit price.

The reference date is based on the data window rather than the current system date, which makes comparisons within a fixed dataset reproducible.

## 5. Customer segmentation
The RFM features are transformed using `log1p` and standardized before K-Means clustering. The default number of clusters is five, but it should be treated as a configurable starting point. The resulting cluster labels are arbitrary identifiers; cluster profiles should be reviewed using recency, frequency, monetary value, and customer counts before assigning business interpretations.

## 6. Product recommendation approach
The included recommender ranks products within each customer cluster by the number of distinct customers who purchased each product, with total units sold used as a tie-breaker. When a customer is selected, products already found in their purchase history can be filtered out.

This is a transparent baseline designed to be easy to explain. It is not a transformer-based semantic recommender and should not be described as a validated predictive model. Product recommendations require offline evaluation before any claim about effectiveness can be made.

## 7. Outputs
After running the pipeline, the following CSV files are generated:

1. `cleaned_transactions.csv`
2. `customer_segments.csv`
3. `cluster_product_recommendations.csv`

The notebook and dashboard provide ways to inspect these outputs. Actual values and visualizations depend on the dataset supplied by the user and are not pre-filled in this report.

## 8. Testing
Unit tests use a small synthetic dataset to check data cleaning, RFM calculations, clustering, recommendation table structure, and invalid-input handling. Run them with `pytest -q`.

## 9. Limitations and future work
- Compare candidate cluster counts with silhouette scores and business interpretability.
- Evaluate recommendations on a time-based holdout using precision@k, recall@k, or MAP@k.
- Handle returns and cancellations in a separate analytical path.
- Compare the baseline with association rules, item-item collaborative filtering, or content-based embeddings.
- Add model persistence and experiment tracking if the project is used repeatedly.
- Apply suitable privacy controls before processing customer data in a production setting.

## 10. Conclusion
The project provides an end-to-end foundation for retail customer segmentation and interpretable product recommendations. It includes reusable functions, command-line execution, a notebook, a lightweight Streamlit interface, and tests. Final business conclusions should be written only after running the workflow on the selected dataset and reviewing the measured results.

## References
- UCI Machine Learning Repository, Online Retail dataset: https://archive.ics.uci.edu/dataset/352/online+retail
- Scikit-learn documentation, K-Means clustering: https://scikit-learn.org/stable/modules/clustering.html#k-means
