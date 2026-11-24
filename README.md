# MLOps Practices 3 and 4

Репозиторий содержит решения практических работ №3 и №4 по дисциплине MLOps.

## Структура проекта

```text
mlops-data-Aprelikova/
├── data/                       # Датасет Wine
├── data.dvc                    # DVC-файл датасета
├── prepare_data.py             # Подготовка данных
├── practice_4/
│   ├── run_experiments.py      # Запуск экспериментов MLflow
│   ├── register_clearml.py     # Регистрация модели в ClearML
│   ├── best_model.joblib       # Лучшая модель
│   ├── comparison.csv          # Сравнение экспериментов
│   └── verification.json       # Результаты проверки модели
├── REPORT.md                   # Отчёт по практическим работам
├── README.md                   # Инструкция по работе с проектом
├── pyproject.toml              # Зависимости проекта
└── poetry.lock                 # Зафиксированные версии зависимостей
```

## Требования

- Python 3.12
- Poetry
- Git
- Доступ к ClearML для работы с датасетами и моделями

## Установка окружения

Клонировать репозиторий:

```bash
git clone <repository-url>
cd mlops-data-Aprelikova
```

Установить зависимости:

```bash
poetry install
```

Команды проекта можно выполнять через `poetry run`, например:

```bash
poetry run python --version
```

## Восстановление данных через DVC

Датасет Wine отслеживается с помощью DVC.

В конфигурации `.dvc/config` используется удалённое хранилище:

```text
../../dvc-remote-storage
```

Для восстановления данных необходимо, чтобы DVC-хранилище было доступно по указанному относительному пути.

Получить данные:

```bash
poetry run dvc pull
```

Проверить состояние данных:

```bash
poetry run dvc status
```

Если хранилище недоступно, необходимо восстановить его расположение или настроить собственный DVC remote.

## Практика 3

В третьей практике выполняется подготовка и версионирование датасета Wine с использованием DVC и ClearML.

- **ClearML Dataset ID:** `b98b2f92d7ac4ac8a462cda305e6256c`
- **SHA-256:** `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60`

## Практика 4. Эксперименты и регистрация модели

В четвёртой практике сравниваются модели Logistic Regression и Random Forest с использованием MLflow.

Проведено шесть экспериментов: три для Logistic Regression и три для Random Forest.

### Запуск экспериментов

Из корневой директории проекта выполнить:

```bash
poetry run python practice_4/run_experiments.py --tracking-uri "sqlite:///C:/proga/ЩАС/MLUPS/experiments/practice_3/Aprelikova/mlops-data-Aprelikova/mlflow.db" --dataset-id "b98b2f92d7ac4ac8a462cda305e6256c" --expected-sha256 "38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60"
```

Скрипт:
1. Загружает датасет по ClearML Dataset ID.
2. Проверяет SHA-256 датасета.
3. Выполняет стратифицированное разбиение данных.
4. Обучает модели и записывает результаты в MLflow.
5. Выбирает лучшую модель по weighted F1 на validation.
6. Вычисляет метрики на test.
7. Проверяет загруженную модель и сохраняет `verification.json`.

При повторном запуске создаются новые MLflow runs.

### Результаты экспериментов

Лучшая модель — Random Forest со следующими параметрами:

- `n_estimators = 100`
- `max_depth = None`
- `min_samples_leaf = 1`
- `random_state = 42`

- **MLflow Experiment ID:** `1`
- **Best Run ID:** `78d2c24d82d54e2082718b07ad334a07`
- **Validation F1:** `0.972369`
- **Test F1:** `0.944444`

### Регистрация модели в ClearML

Лучшая модель зарегистрирована и опубликована в ClearML.

- **Project:** `MIIT/MLOps/practice_4/Aprelikova`
- **Task:** `wine-best-model`
- **Task ID:** `87a2e4b09ba04579be78ae4ce35310c2`
- **Model ID:** `5c9f8f30698a45a1bd822e7b50039e74`

Для регистрации используется скрипт:

```bash
poetry run python practice_4/register_clearml.py
```

Для работы с ClearML необходимо предварительно настроить учётные данные.

## Проверка модели

Результаты проверки лучшей модели находятся в `practice_4/verification.json`.

Проверены:
- наличие MLflow signature;
- совпадение предсказаний исходной и повторно загруженной модели;
- наличие обязательных параметров и метрик;
- вычисление метрик на тестовой выборке.

Подробные результаты и таблица сравнения моделей представлены в [REPORT.md](REPORT.md).