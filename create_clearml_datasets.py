import argparse
from clearml import Dataset

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["base", "wine", "iris_features"])
    parser.add_argument("--base-id", default=None)
    parser.add_argument("--project", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    if args.step == "base":
        ds = Dataset.create(
            dataset_project=args.project,
            dataset_name=args.name,
            dataset_version="1.0.0",
            dataset_tags=["base"],
            description="Base version with original Iris",
        )
        ds.add_files(path="data/iris.csv")
        ds.upload()
        ds.finalize()
        print("BASE_ID:", ds.id)
        print("Files:", ds.list_files())
    elif args.step == "wine":
        if not args.base_id:
            raise ValueError("--base-id required for wine")
        ds = Dataset.create(
            dataset_project=args.project,
            dataset_name=args.name,
            dataset_version="1.1.0",
            parent_datasets=[args.base_id],
            dataset_tags=["wine"],
            description="Child version that adds Wine",
        )
        ds.add_files(path="data/wine.csv")
        ds.upload()
        ds.finalize()
        print("WINE_ID:", ds.id)
        print("All files:", ds.list_files())
        print("Added files:", ds.list_added_files())
        print("Lineage:", ds.get_dependency_graph())
    elif args.step == "iris_features":
        if not args.base_id:
            raise ValueError("--base-id required for iris_features")
        ds = Dataset.create(
            dataset_project=args.project,
            dataset_name=args.name,
            dataset_version="2.0.0",
            parent_datasets=[args.base_id],
            dataset_tags=["iris_features"],
            description="Branch from base with iris area features",
        )
        ds.add_files(path="data/iris.csv")
        ds.upload()
        ds.finalize()
        print("IRIS_FEATURES_ID:", ds.id)
        print("All files:", ds.list_files())
        print("Modified files:", ds.list_modified_files())
        print("Lineage:", ds.get_dependency_graph())

if __name__ == "__main__":
    main()