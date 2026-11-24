
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import mlflow.pyfunc
import pandas as pd

from clearml import Dataset
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# НАСТРОЙКИ
# ============================================================

EXPERIMENT_NAME = "miit-mlops-practice-4-aprelikova"

DEFAULT_DATASET_ID = "b98b2f92d7ac4ac8a462cda305e6256c"

EXPECTED_SHA256 = (
    "38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60"
)

RANDOM_STATE = 42

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = Path(__file__).resolve().parent

COMPARISON_PATH = OUTPUT_DIR / "comparison.csv"

VERIFICATION_PATH = OUTPUT_DIR / "verification.json"

BEST_MODEL_PATH = OUTPUT_DIR / "best_model.joblib"


# ============================================================
# КОНФИГУРАЦИИ МОДЕЛЕЙ
# ============================================================

def get_model_configs():

    configs = []

    # Logistic Regression: три варианта C

    for c in [0.1, 1.0, 10.0]:

        configs.append({
            "name": f"logistic_regression_C_{c}",
            "family": "LogisticRegression",
            "model": Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(
                    C=c,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                )),
            ]),
            "params": {
                "model_type": "LogisticRegression",
                "C": c,
                "solver": "lbfgs",
                "max_iter": 1000,
                "random_state": RANDOM_STATE,
            },
        })

    # Random Forest: три варианта параметров

    rf_configs = [
        {
            "n_estimators": 100,
            "max_depth": None,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 200,
            "max_depth": 5,
            "min_samples_leaf": 1,
        },
        {
            "n_estimators": 200,
            "max_depth": None,
            "min_samples_leaf": 2,
        },
    ]

    for index, params in enumerate(rf_configs, start=1):

        configs.append({
            "name": f"random_forest_{index}",
            "family": "RandomForest",
            "model": RandomForestClassifier(
                **params,
                random_state=RANDOM_STATE,
            ),
            "params": {
                "model_type": "RandomForest",
                **params,
                "random_state": RANDOM_STATE,
            },
        })

    return configs


# ============================================================
# ЗАГРУЗКА И ПРОВЕРКА ДАТАСЕТА
# ============================================================

def calculate_sha256(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_dataset(dataset_id, expected_sha256):

    print("Получаем Dataset из ClearML...")

    dataset = Dataset.get(dataset_id=dataset_id)

    dataset_path = Path(dataset.get_local_copy())

    print("Dataset ID:", dataset_id)

    csv_files = list(dataset_path.rglob("wine.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"Файл wine.csv не найден в {dataset_path}"
        )

    csv_path = csv_files[0]

    actual_sha256 = calculate_sha256(csv_path)

    print("SHA-256:", actual_sha256)

    if actual_sha256 != expected_sha256:

        raise RuntimeError(
            "SHA-256 датасета не совпадает с ожидаемым! "
            "Обучение остановлено."
        )

    print("Хэш совпадает. Данные проверены.")

    df = pd.read_csv(csv_path)

    if "target" not in df.columns:
        raise ValueError("В датасете отсутствует столбец target.")

    if df.isnull().any().any():
        raise ValueError("В датасете обнаружены пропущенные значения.")

    return df, actual_sha256


# ============================================================
# РАЗДЕЛЕНИЕ ДАННЫХ
# ============================================================

def split_dataset(df):

    X = df.drop(columns=["target"])

    y = df["target"]

    # Сначала выделяем 20% тестовой выборки

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # Из оставшихся 80% выделяем 25% для validation.
    # Получаем итоговые пропорции 60 / 20 / 20.

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=y_train_val,
    )

    print(
        "Размеры выборок:",
        len(X_train),
        len(X_val),
        len(X_test),
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


# ============================================================
# МЕТРИКИ
# ============================================================

def calculate_metrics(y_true, predictions):

    return {
        "accuracy": float(
            accuracy_score(y_true, predictions)
        ),
        "precision_weighted": float(
            precision_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "recall_weighted": float(
            recall_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
        "f1_weighted": float(
            f1_score(
                y_true,
                predictions,
                average="weighted",
                zero_division=0,
            )
        ),
    }


# ============================================================
# ОБУЧЕНИЕ И ЛОГИРОВАНИЕ МОДЕЛЕЙ В MLFLOW
# ============================================================

def run_experiments(
    X_train,
    X_val,
    y_train,
    y_val,
    dataset_id,
    dataset_sha256,
):

    current_run_ids = []

    configs = get_model_configs()

    for config in configs:

        print()
        print("Запуск:", config["name"])

        with mlflow.start_run(run_name=config["name"]) as run:

            run_id = run.info.run_id

            current_run_ids.append(run_id)

            model = config["model"]

            # Обучение

            start_time = time.perf_counter()

            model.fit(X_train, y_train)

            training_time = time.perf_counter() - start_time

            # Оценка только на validation

            predictions = model.predict(X_val)

            metrics = calculate_metrics(y_val, predictions)

            # Параметры

            mlflow.log_params(config["params"])

            # Время обучения

            mlflow.log_metric(
                "training_time",
                training_time,
            )

            # Метрики validation

            for metric_name, metric_value in metrics.items():

                mlflow.log_metric(
                    f"val_{metric_name}",
                    metric_value,
                )

            # Теги

            mlflow.set_tags({
                "model_family": config["family"],
                "dataset_id": dataset_id,
                "dataset_sha256": dataset_sha256,
            })

            # Signature и пример входных данных

            input_example = X_train.head(5)

            signature = infer_signature(
                input_example,
                model.predict(input_example),
            )

            # Сохранение модели.
            # Random Forest использует внутренний тип Tree.
            # Разрешаем только этот конкретный тип.

            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                signature=signature,
                input_example=input_example,
                skops_trusted_types=[
                    "sklearn.tree._tree.Tree"
                ],
            )

            print("Validation F1:", metrics["f1_weighted"])

            print("Время обучения:", training_time)

            print("Run ID:", run_id)

    return current_run_ids


# ============================================================
# ВЫБОР ЛУЧШЕЙ МОДЕЛИ ПО VALIDATION F1
# ============================================================

def select_best_run(dataset_id, dataset_sha256):

    experiment = mlflow.get_experiment_by_name(
        EXPERIMENT_NAME
    )

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=(
            f"tags.dataset_id = '{dataset_id}' "
            f"and tags.dataset_sha256 = '{dataset_sha256}'"
        ),
        order_by=["metrics.val_f1_weighted DESC"],
    )

    if runs.empty:
        raise RuntimeError(
            "MLflow не вернул ни одного запуска."
        )

    if runs["metrics.val_f1_weighted"].isna().all():
        raise RuntimeError(
            "Не найдены значения validation F1."
        )

    best_run = runs.iloc[0]

    best_run_id = best_run["run_id"]

    print()
    print("Лучшая модель:", best_run["tags.mlflow.runName"])

    print("Best Run ID:", best_run_id)

    print(
        "Best Validation F1:",
        best_run["metrics.val_f1_weighted"],
    )

    return best_run_id, runs


# ============================================================
# ТАБЛИЦА СРАВНЕНИЯ МОДЕЛЕЙ
# ============================================================

def create_comparison_table(runs):

    comparison = pd.DataFrame()

    comparison["run_id"] = runs["run_id"]

    comparison["model_family"] = runs["tags.model_family"]

    comparison["run_name"] = runs["tags.mlflow.runName"]

    comparison["validation_f1"] = runs[
        "metrics.val_f1_weighted"
    ]

    comparison["training_time"] = runs[
        "metrics.training_time"
    ]

    comparison["model_type"] = runs.get(
        "params.model_type"
    )

    comparison["C"] = runs.get(
        "params.C"
    )

    comparison["n_estimators"] = runs.get(
        "params.n_estimators"
    )

    comparison["max_depth"] = runs.get(
        "params.max_depth"
    )

    comparison.to_csv(
        COMPARISON_PATH,
        index=False,
    )

    print()
    print("Таблица сравнения сохранена:", COMPARISON_PATH)

    return comparison


# ============================================================
# ПРОВЕРКА ЛУЧШЕЙ МОДЕЛИ
# ============================================================

def verify_best_model(
    best_run_id,
    X_test,
    y_test,
    dataset_id,
    dataset_sha256,
):

    model_uri = f"runs:/{best_run_id}/model"

    print()
    print("Загружаем лучшую модель:", model_uri)

    # Загрузка sklearn-модели

    sklearn_model = mlflow.sklearn.load_model(model_uri)

    # Проверка исходных названий столбцов

    expected_columns = list(X_test.columns)

    if list(X_test.columns) != expected_columns:
        raise RuntimeError(
            "Названия столбцов изменились."
        )

    # Предсказания sklearn

    sklearn_predictions = sklearn_model.predict(X_test)

    # Загрузка через pyfunc

    pyfunc_model = mlflow.pyfunc.load_model(model_uri)

    pyfunc_predictions = pyfunc_model.predict(X_test)

    # Проверка совпадения предсказаний

    predictions_match = bool(
        (sklearn_predictions == pyfunc_predictions).all()
    )

    if not predictions_match:
        raise RuntimeError(
            "Предсказания sklearn и pyfunc не совпадают."
        )

    print("Совпадение предсказаний: OK")

    # Проверка signature

    model_info = mlflow.models.get_model_info(model_uri)

    signature = model_info.signature

    if signature is None:
        raise RuntimeError(
            "У модели отсутствует signature."
        )

    signature_columns = [
        field.name for field in signature.inputs
    ]

    if signature_columns != expected_columns:
        raise RuntimeError(
            "Signature не соответствует исходным столбцам."
        )

    print("Проверка signature: OK")

    # Тестовая оценка выполняется только после выбора модели

    test_metrics = calculate_metrics(
        y_test,
        sklearn_predictions,
    )

    print()
    print("Test metrics:")

    for name, value in test_metrics.items():
        print(f"{name}: {value}")

    # Записываем test-метрики в выбранный MLflow run

    client = MlflowClient()

    for name, value in test_metrics.items():

        client.log_metric(
            best_run_id,
            f"test_{name}",
            value,
        )

    # Сохраняем локальную копию модели

    joblib.dump(
        sklearn_model,
        BEST_MODEL_PATH,
    )

    # Проверяем обязательные параметры и метрики

    best_run = client.get_run(best_run_id)

    required_params = [
        "model_type",
        "random_state",
    ]

    for param in required_params:

        if param not in best_run.data.params:
            raise RuntimeError(
                f"Отсутствует обязательный параметр: {param}"
            )

    required_metrics = [
        "val_accuracy",
        "val_precision_weighted",
        "val_recall_weighted",
        "val_f1_weighted",
        "training_time",
        "test_accuracy",
        "test_precision_weighted",
        "test_recall_weighted",
        "test_f1_weighted",
    ]

    for metric in required_metrics:

        if metric not in best_run.data.metrics:
            raise RuntimeError(
                f"Отсутствует обязательная метрика: {metric}"
            )

    # Итоговая проверка

    verification = {
        "status": "passed",
        "best_run_id": best_run_id,
        "model_uri": model_uri,
        "dataset_id": dataset_id,
        "dataset_sha256": dataset_sha256,
        "signature_valid": True,
        "prediction_parity": predictions_match,
        "required_params_valid": True,
        "required_metrics_valid": True,
        "test_metrics": test_metrics,
    }

    with open(
        VERIFICATION_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            verification,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # Логируем verification.json в MLflow

    with mlflow.start_run(
        run_id=best_run_id
    ):

        mlflow.log_artifact(
            str(VERIFICATION_PATH)
        )

    print()
    print("Проверка завершена успешно.")

    print("Verification:", VERIFICATION_PATH)

    print("Model:", BEST_MODEL_PATH)

    return test_metrics


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI"),
    )

    parser.add_argument(
        "--dataset-id",
        default=os.getenv(
            "CLEARML_DATASET_ID",
            DEFAULT_DATASET_ID,
        ),
    )

    parser.add_argument(
        "--expected-sha256",
        default=os.getenv(
            "EXPECTED_DATASET_SHA256",
            EXPECTED_SHA256,
        ),
    )

    args = parser.parse_args()

    # Настройка MLflow

    if args.tracking_uri:

        tracking_uri = args.tracking_uri

    else:

        db_path = ROOT_DIR / "mlflow.db"

        tracking_uri = (
            f"sqlite:///{db_path.as_posix()}"
        )

    mlflow.set_tracking_uri(tracking_uri)

    mlflow.set_experiment(EXPERIMENT_NAME)

    print("MLflow Tracking URI:", tracking_uri)

    print("Experiment:", EXPERIMENT_NAME)

    # Загрузка и проверка датасета

    df, dataset_sha256 = load_dataset(
        args.dataset_id,
        args.expected_sha256,
    )

    # Разделение данных

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    ) = split_dataset(df)

    # Обучение моделей

    run_ids = run_experiments(
        X_train,
        X_val,
        y_train,
        y_val,
        args.dataset_id,
        dataset_sha256,
    )

    if len(run_ids) < 6:
        raise RuntimeError(
            "Обучено меньше шести моделей."
        )

    # Выбор лучшей модели по validation

    best_run_id, runs = select_best_run(
        args.dataset_id,
        dataset_sha256,
    )

    # Таблица сравнения

    comparison = create_comparison_table(runs)

    print()
    print(comparison.to_string(index=False))

    # Проверка лучшей модели и однократная оценка на test

    test_metrics = verify_best_model(
        best_run_id,
        X_test,
        y_test,
        args.dataset_id,
        dataset_sha256,
    )

    # Итог

    experiment = mlflow.get_experiment_by_name(
        EXPERIMENT_NAME
    )

    print()
    print("=" * 55)

    print("ЭКСПЕРИМЕНТ УСПЕШНО ЗАВЕРШЁН")

    print("Experiment ID:", experiment.experiment_id)

    print("Best Run ID:", best_run_id)

    print("Test F1:", test_metrics["f1_weighted"])

    print("=" * 55)


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print()
        print("ОШИБКА:", error)

        raise
