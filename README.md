# Retail Customer Segmentation & Product Recommendations

**Author:** Touseeq Danish  
**Focus:** retail analytics, RFM customer segmentation, K-Means clustering, and cluster-based product recommendations.

## Overview

This project analyzes retail transaction data to understand customer purchasing behavior. It calculates **Recency, Frequency, and Monetary (RFM)** features, segments customers using K-Means, and produces transparent product recommendations based on products purchased by customers in each segment.

The repository includes a reusable Python pipeline, an exploratory Jupyter notebook, a Streamlit dashboard, tests, and a project report/presentation.

> **Important:** The source dataset is not included. The repository does not contain verified run results, so no accuracy or business-impact claims are made. Run the workflow on the dataset to generate the output tables.

## Features

- Load CSV and Excel transaction data.
- Validate required columns and standardize common data types.
- Exclude records with missing customer identifiers and non-positive quantities/prices from the positive-sales analysis.
- Calculate customer-level RFM features:
  - **Recency:** days since last purchase, relative to one day after the latest transaction date.
  - **Frequency:** number of distinct invoices.
  - **Monetary:** total transaction revenue (`Quantity × UnitPrice`).
- Apply `log1p`, standardization, and K-Means clustering to RFM features.
- Recommend popular products within each customer cluster, ranked by the number of distinct customers who purchased them, with units sold as a tie-breaker.
- Filter recommendations to remove products already purchased by a selected customer.
- Export cleaned data, customer segments, and recommendation tables.
- Explore results through a Streamlit app.

## Repository structure

```text
client-segmentation-product-recommendation/
├── app.py
├── requirements.txt
├── README.md
├── REPORT.md
├── report.pdf
├── LICENSE
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   └── run_pipeline.py
├── notebooks/
│   └── customer_segmentation_recommendation.ipynb
├── tests/
│   └── test_pipeline.py
├── data/
│   └── (place the dataset here; data files are not committed)
├── outputs/
│   └── (generated CSV files; ignored by Git)
└── presentation/
    └── Report_R_F_M.pptx
```

## Dataset

This project is designed for the **Online Retail** dataset from the UCI Machine Learning Repository:

https://archive.ics.uci.edu/dataset/352/online+retail

Download the dataset and place the Excel file at `data/OnlineRetail.xlsx`, or use a CSV export. Do not commit raw customer-level transaction data unless you have checked the dataset licence and privacy implications.

Expected columns:

| Column | Required? | Meaning |
|---|---|---|
| `InvoiceNo` | Yes | Transaction/invoice identifier |
| `Description` | Yes | Product description |
| `Quantity` | Yes | Units purchased |
| `InvoiceDate` | Yes | Date/time of transaction |
| `UnitPrice` | Yes | Price per unit |
| `CustomerID` | Yes | Customer identifier |
| `StockCode` | No | Product code |
| `Country` | No | Customer country |

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the pipeline

From the repository root:

```bash
python src/run_pipeline.py --input data/OnlineRetail.xlsx --output-dir outputs --clusters 5 --top-n 10
```

For a CSV input:

```bash
python src/run_pipeline.py --input data/online_retail.csv
```

Generated files:

- `outputs/cleaned_transactions.csv`
- `outputs/customer_segments.csv`
- `outputs/cluster_product_recommendations.csv`

## Run the notebook

Open `notebooks/customer_segmentation_recommendation.ipynb` in Jupyter or VS Code. Run cells from top to bottom after placing the dataset in `data/`.

## Run the dashboard

```bash
streamlit run app.py
```

Upload a CSV or Excel file with the required columns. The dashboard displays the cleaned-data counts, customer segments, cluster profiles, and recommendations, and lets you download results.

## Run tests

```bash
pytest -q
```

Tests use a small synthetic dataset and do not require the real Online Retail file.

## Methodology and caveats

### Data cleaning
Customer IDs are not imputed because there is no reliable basis for assigning a missing transaction to a customer. Rows with non-positive quantities or unit prices are excluded from this positive-sales workflow; returns and cancellations should be analyzed separately if they are relevant to the business question.

### RFM and clustering
The RFM values are transformed with `log1p` and standardized before K-Means. The default of five clusters is a starting point, not a universally optimal choice. Compare cluster counts using measures such as silhouette score and, crucially, interpretability for the business. K-Means cluster numbers are arbitrary labels and must not be interpreted as a ranking by themselves.

### Recommendations
The included recommender is a **cluster-level popularity baseline**. It suggests products that other customers in the same RFM cluster purchased frequently. It does not train a neural or transformer model, and it does not prove that a customer will buy a recommended item. New customers and small clusters may have limited recommendations. A stronger future version could evaluate item-based collaborative filtering, association rules, or content embeddings using a time-based holdout set.

## Limitations and future improvements

- Add a validation strategy and compare multiple cluster counts systematically.
- Evaluate recommendations with precision@k, recall@k, or MAP@k on held-out transactions.
- Analyze returns/cancellations separately rather than discarding them.
- Add model persistence, experiment tracking, and configurable reference dates.
- Consider privacy and access controls before deploying with real customer data.

## License

The code is provided under the MIT License in `LICENSE`. This does not change the terms or attribution requirements of the external dataset.
