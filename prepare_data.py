import argparse
from pathlib import Path
import pandas as pd
from sklearn.datasets import load_iris, load_wine

def save_frame(frame, path, sort_by=None):
    if sort_by is None:
        sort_by = list(frame.columns)
    ordered = frame.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["base", "wine", "iris_features"])
    args = parser.parse_args()

    data_dir = Path("data")
    iris_path = data_dir / "iris.csv"
    wine_path = data_dir / "wine.csv"

    if args.mode == "base":
        iris = load_iris(as_frame=True).frame
        save_frame(iris, iris_path)
        print(f"Saved base iris to {iris_path}")
    elif args.mode == "wine":
        wine = load_wine(as_frame=True).frame
        save_frame(wine, wine_path)
        print(f"Saved wine to {wine_path}")
    elif args.mode == "iris_features":
        iris = load_iris(as_frame=True).frame
        original_cols = list(iris.columns)
        iris["sepal_area"] = iris["sepal length (cm)"] * iris["sepal width (cm)"]
        iris["petal_area"] = iris["petal length (cm)"] * iris["petal width (cm)"]
        iris = iris[original_cols + ["sepal_area", "petal_area"]]
        save_frame(iris, iris_path, sort_by=original_cols)
        print(f"Saved iris with features to {iris_path}")

if __name__ == "__main__":
    main()