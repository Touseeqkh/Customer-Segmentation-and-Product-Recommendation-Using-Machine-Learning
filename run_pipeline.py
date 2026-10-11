"""Run the customer segmentation and recommendation pipeline from the command line."""
import argparse
from pathlib import Path
import sys

import pandas as pd

# Support running as `python src/run_pipeline.py` from repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pipeline import (
    load_retail_data, clean_retail_data, calculate_rfm,
    cluster_customers, generate_cluster_recommendations,
)


def main():
    parser = argparse.ArgumentParser(description="Segment retail customers and recommend products by cluster.")
    parser.add_argument("--input", required=True, help="Path to Online Retail CSV or Excel file.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for CSV outputs.")
    parser.add_argument("--clusters", type=int, default=5, help="Number of customer clusters (default: 5).")
    parser.add_argument("--top-n", type=int, default=10, help="Recommendations to save per cluster.")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = load_retail_data(args.input)
    clean = clean_retail_data(raw)
    rfm = calculate_rfm(clean)
    segmented, _, _ = cluster_customers(rfm, n_clusters=args.clusters)
    recs = generate_cluster_recommendations(clean, segmented, top_n=args.top_n)

    clean.to_csv(out / "cleaned_transactions.csv", index=False)
    segmented.to_csv(out / "customer_segments.csv", index=False)
    recs.to_csv(out / "cluster_product_recommendations.csv", index=False)
    print(f"Input rows: {len(raw):,}")
    print(f"Clean sales rows: {len(clean):,}")
    print(f"Customers segmented: {len(segmented):,}")
    print(f"Clusters produced: {segmented['Cluster'].nunique()}")
    print(f"Recommendations saved: {len(recs):,}")
    print(f"Output directory: {out.resolve()}")


if __name__ == "__main__":
    main()
