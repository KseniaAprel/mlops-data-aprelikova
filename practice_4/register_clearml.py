
import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient
from clearml import Task, OutputModel


# Пути и идентификаторы практики
BASE_DIR = Path(__file__).resolve().parent
TASK_ID = "87a2e4b09ba04579be78ae4ce35310c2"
DATASET_ID = "b98b2f92d7ac4ac8a462cda305e6256c"
DATASET_SHA256 = "38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60"

TRACKING_URI = (
    "sqlite:///C:/proga/ЩАС/MLUPS/experiments/"
    "practice_3/Aprelikova/mlops-data-Aprelikova/mlflow.db"
)

# Файлы
comparison_path = BASE_DIR / "comparison.csv"
verification_path = BASE_DIR / "verification.json"
model_path = BASE_DIR / "best_model.joblib"

for path in [comparison_path, verification_path, model_path]:
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл: {path}")

# MLflow: определяем лучший запуск по validation F1
mlflow.set_tracking_uri(TRACKING_URI)
client = MlflowClient()

comparison = pd.read_csv(comparison_path)
comparison = comparison.dropna(subset=["validation_f1"])
comparison = comparison.sort_values("validation_f1", ascending=False)

if len(comparison) < 6:
    raise RuntimeError("В comparison.csv должно быть не менее 6 завершённых запусков")

comparison.to_csv(comparison_path, index=False)

best_run_id = str(comparison.iloc[0]["run_id"])
best_run = client.get_run(best_run_id)

# Проверяем результат предыдущей верификации
with open(verification_path, encoding="utf-8") as f:
    verification = json.load(f)

if verification.get("status") != "passed":
    raise RuntimeError("Проверка модели не пройдена")

if verification.get("best_run_id") != best_run_id:
    raise RuntimeError("Run ID в verification.json не совпадает с лучшим запуском")

if verification.get("dataset_id") != DATASET_ID:
    raise RuntimeError("Dataset ID не совпадает")

if verification.get("dataset_sha256") != DATASET_SHA256:
    raise RuntimeError("SHA-256 не совпадает")

# Получаем параметры и метрики из MLflow
params = dict(best_run.data.params)
metrics = dict(best_run.data.metrics)

required_metrics = [
    "val_accuracy",
    "val_precision_weighted",
    "val_recall_weighted",
    "val_f1_weighted",
    "test_accuracy",
    "test_precision_weighted",
    "test_recall_weighted",
    "test_f1_weighted",
]

for name in required_metrics:
    if name not in metrics:
        raise RuntimeError(f"В MLflow отсутствует метрика {name}")

params["mlflow_run_id"] = best_run_id
params["clearml_dataset_id"] = DATASET_ID
params["dataset_sha256"] = DATASET_SHA256

# Проверяем классы модели
model = joblib.load(model_path)
classes = model.named_steps["model"].classes_ if hasattr(model, "named_steps") else model.classes_
labels = {f"class_{int(value)}": int(value) for value in classes}

# Получаем существующую ClearML Task
task = Task.get_task(task_id=TASK_ID)

if task is None:
    raise RuntimeError("Не удалось получить ClearML Task")

if task.get_status() != "in_progress":
    task.mark_started(force=True)

# Передаём параметры
task.connect(params, name="best_model_params")

# Передаём метрики
logger = task.get_logger()

for metric_name in required_metrics:
    if metric_name.startswith("val_"):
        title = "validation"
        series = metric_name.removeprefix("val_")
    else:
        title = "test"
        series = metric_name.removeprefix("test_")

    logger.report_scalar(
        title=title,
        series=series,
        value=float(metrics[metric_name]),
        iteration=0,
    )

logger.report_scalar(
    title="training",
    series="training_time",
    value=float(metrics["training_time"]),
    iteration=0,
)

# Прикрепляем артефакты к задаче
for artifact_name, artifact_path in [
    ("verification.json", verification_path),
    ("comparison.csv", comparison_path),
    ("best_model.joblib", model_path),
]:
    result = task.upload_artifact(
        name=artifact_name,
        artifact_object=str(artifact_path),
        wait_on_upload=True,
    )
    if not result:
        raise RuntimeError(f"Не удалось загрузить {artifact_name}")

# Создаём OutputModel
output_model = OutputModel(
    task=task,
    name="wine-best-model",
    framework="scikit-learn",
    label_enumeration=labels,
    tags=["wine", "practice-4", "random-forest"],
    comment=f"Best MLflow run: {best_run_id}",
)

# Загружаем файл модели
output_model.update_weights(
    weights_filename=str(model_path),
    auto_delete_file=False,
    async_enable=False,
)

# Метаданные модели
metadata = {
    "mlflow_run_id": best_run_id,
    "clearml_dataset_id": DATASET_ID,
    "dataset_sha256": DATASET_SHA256,
    "model_family": "RandomForest",
}

for key, value in metadata.items():
    if not output_model.set_metadata(key, str(value)):
        raise RuntimeError(f"Не удалось записать metadata: {key}")

# Публикуем только после проверки и загрузки
output_model.publish()

# Завершаем задачу
task.mark_completed(
    status_message="Best Wine model verified and published",
    force=True,
)

print("\nCLEARML REGISTRATION SUCCESSFUL")
print("Task ID:", TASK_ID)
print("MLflow Run ID:", best_run_id)
print("Model ID:", output_model.id)
print("Dataset ID:", DATASET_ID)
print("Validation F1:", metrics["val_f1_weighted"])
print("Test F1:", metrics["test_f1_weighted"])
