import hashlib
from pathlib import Path
from clearml import Dataset
import pandas as pd

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def describe_csv(path):
    df = pd.read_csv(path)
    return {
        "file": path.name,
        "sha256": sha256_file(path),
        "rows": len(df),
        "cols": len(df.columns),
        "missing": int(df.isna().sum().sum()),
        "columns": list(df.columns),
    }

def main():
    ids = {
        "1.0.0": "b776397a5fb642fcb2895ae897449091",
        "1.1.0": "b98b2f92d7ac4ac8a462cda305e6256c",
        "2.0.0": "776a29a536d348d6aeb36546ca1c3e8b",
    }
    base_dir = Path("clearml_downloads")
    for version, ds_id in ids.items():
        target = base_dir / version.replace(".", "_")
        print(f"\n=== Downloading version {version} ({ds_id}) ===")
        ds = Dataset.get(dataset_id=ds_id)
        print(f"Version: {version}")
        print(f"Parent IDs: {ds.get_parent_datasets() if hasattr(ds, 'get_parent_datasets') else 'n/a'}")
        # Используем get_mutable_local_copy для скачивания
        local_path = ds.get_mutable_local_copy(target_folder=str(target), overwrite=True)
        print(f"Downloaded to: {local_path}")
        print("Files in download:")
        for csv_path in sorted(Path(local_path).rglob("*.csv")):
            info = describe_csv(csv_path)
            print(f"  {info}")

if __name__ == "__main__":
    main()