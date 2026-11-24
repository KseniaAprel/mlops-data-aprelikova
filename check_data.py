import hashlib
from pathlib import Path
import pandas as pd

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def check_file(path, expected_rows=None):
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    df = pd.read_csv(path)
    if any(str(col).startswith("Unnamed") for col in df.columns):
        raise ValueError(f"Unnamed index column found in {path}")
    if expected_rows is not None and len(df) != expected_rows:
        raise ValueError(f"Row count mismatch for {path}: {len(df)} != {expected_rows}")
    print(f"--- {path} ---")
    print(f"SHA-256: {sha256_file(path)}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Missing: {df.isna().sum().sum()}")
    return df

def main():
    data_dir = Path("data")
    iris_path = data_dir / "iris.csv"
    wine_path = data_dir / "wine.csv"

    iris_df = check_file(iris_path, expected_rows=150)
    if "sepal_area" in iris_df.columns:
        expected_sepal = iris_df["sepal length (cm)"] * iris_df["sepal width (cm)"]
        if not (iris_df["sepal_area"] == expected_sepal).all():
            raise ValueError("sepal_area incorrect")
    if "petal_area" in iris_df.columns:
        expected_petal = iris_df["petal length (cm)"] * iris_df["petal width (cm)"]
        if not (iris_df["petal_area"] == expected_petal).all():
            raise ValueError("petal_area incorrect")

    if wine_path.exists():
        check_file(wine_path, expected_rows=178)
    else:
        print("wine.csv not present (ok for base)")

if __name__ == "__main__":
    main()