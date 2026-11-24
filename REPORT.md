# Отчёт по практике 3. Версионирование данных с DVC и ClearML

## Версии данных

### Окружение

- Python: 3.12
- DVC: 3.67.1
- ClearML: 2.2.0
- scikit-learn: 1.9.1
- pandas: 3.1.1
- Git: 2.46.0.windows.1

Ссылка на Git-репозиторий: https://github.com/KseniaAprel/mlops-data-aprelikova

### DVC

**Базовая версия (data-v1):**

- Git commit: `93e9fde5cb38f4a9a26ff92fbc37a0b081f9e1e9`
- Git tag: `data-v1`
- `data.dvc` хэш: `bf5656de288a783265cb7b85509abc8e.dir`
- SHA-256 `data/iris.csv`: `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f`
- Форма iris: (150, 5), столбцы: sepal length (cm), sepal width (cm), petal length (cm), petal width (cm), target
- Пропусков: 0

**DVC remote:**

- Тип: локальная директория вне репозитория
- Путь (относительно репозитория): `..\dvc-remote-storage`
- Секретов нет
- Git commit конфигурации remote: `4487d08`
- В remote отправлено 2 объекта (базовая версия)

**Ветка feature/wine:**

- Git commit: `a21e5c583c5f701d5ce97b933917174c198d8681`
- `data.dvc` хэш: `f8fe844935c3e7d61c8736baacbf1018.dir`
- SHA-256 `data/wine.csv`: `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60`
- Форма wine: (178, 14), пропусков: 0
- SHA-256 iris не изменился: `6d700503...` ✓
- Исправление check_data.py (tolerance для area): `0a5802f5fc9c67128eab572fd8f3429063072a94`

**Объединённая версия (merge feature/wine в feature/iris-features):**

- Merge-коммит: `0bf9fc540fb711b63992e467b45e6849f76462cf`
- `data.dvc` хэш: `957c42d7c9ecafed014287db892a5935.dir`, nfiles=2
- `iris.csv`: SHA-256 `3e1ba63f...` (с признаками), форма (150, 7)
- `wine.csv`: SHA-256 `38860ba0...`, форма (178, 14)
- Слияние автоматическое (DVC merge driver), без маркеров конфликта

**Чистое восстановление:**

- `main` после merge: `0bf9fc540fb711b63992e467b45e6849f76462cf`
- Клон: `mlops-data-clone`, `dvc pull` восстановил оба CSV
- SHA-256 в клоне совпадают: iris `3e1ba63f...`, wine `38860ba0...`
- Восстановление не зависит от старого локального cache ✓

### ClearML Datasets

**Базовый Dataset 1.0.0:**
- BASE_ID: `b776397a5fb642fcb2895ae897449091`
- Содержимое: `['iris.csv']`
- Статус: Completed (финализирован)
- Тег: `base`

**Дочерняя версия 1.1.0 (Wine):**
- WINE_ID: `b98b2f92d7ac4ac8a462cda305e6256c`
- Parent: `b776397a5fb642fcb2895ae897449091` (BASE_ID)
- All files: `['iris.csv', 'wine.csv']`
- Added files: `['wine.csv']`

**Отдельная ветвь 2.0.0 (iris_features):**
- IRIS_FEATURES_ID: `776a29a536d348d6aeb36546ca1c3e8b`
- Parent: `b776397a5fb642fcb2895ae897449091` (BASE_ID, не WINE_ID)
- All files: `['iris.csv']`
- Modified files: `['iris.csv']`

### Скачанные версии ClearML

| Version | Dataset ID | Files | SHA-256 | Shape |
|---|---|---|---|---|
| 1.0.0 | b776397a5fb642fcb2895ae897449091 | iris.csv | 6d700503... | (150, 5) |
| 1.1.0 | b98b2f92d7ac4ac8a462cda305e6256c | iris.csv | 6d700503... | (150, 5) |
| 1.1.0 | b98b2f92d7ac4ac8a462cda305e6256c | wine.csv | 38860ba0... | (178, 14) |
| 2.0.0 | 776a29a536d348d6aeb36546ca1c3e8b | iris.csv | 3e1ba63f... | (150, 7) |

**WINE_SHA256:** `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60`
Совпадение DVC и ClearML: ✅


## Часть 4. Сравнение

### Сравнительная таблица

| Критерий | DVC | ClearML Dataset |
|---|---|---|
| Идентификатор версии | Git commit + хэш в `data.dvc` (`957c42d7...`) | Dataset ID (`b776397a...` и т.д.) |
| Расположение метаданных | `data.dvc` в Git, конфиг в `.dvc/config` | Внутри ClearML Server (БД и файловое хранилище) |
| Расположение файлов | DVC remote (`..\dvc-remote-storage`) | ClearML File Server (files.clear.ml) |
| Создание дочерней версии | Новая ветка + `dvc add` + коммит | `Dataset.create(..., parent_datasets=[ID])` |
| Переключение версии | `git switch` + `dvc checkout` | `Dataset.get(dataset_id=...)` |
| Восстановление на чистой машине | `git clone` + `dvc pull` | `Dataset.get(id).get_mutable_local_copy(...)` |
| Поведение при ветвлении | Git-ветки, DVC merge driver | Lineage-граф с несколькими родителями |
| Поведение при слиянии | Автоматический merge `.dvc` через драйвер | Не применимо (immutable версии), вместо слияния — новая версия от нужного родителя |
| Связь версии данных с Git | Жёсткая: версия определяется коммитом | Слабая: версия существует независимо от Git |
| Доступность через UI | Только через Git-хостинг и файловое хранилище | Веб-интерфейс ClearML (lineage, файлы, метаданные) |

### Вывод (ответы на вопросы)

1. **Какой объект однозначно определяет версию данных в DVC?**
   Хэш директории в `data.dvc` (например, `957c42d7c9ecafed014287db892a5935.dir`). Он указывает на конкретный набор файлов в DVC cache и remote. Git-коммит лишь фиксирует этот хэш в истории.

2. **Почему одного Git-коммита недостаточно без DVC remote?**
   Git хранит только `data.dvc` с хэшем, но не сами CSV. Без remote (или локального cache) данные неоткуда восстановить. В нашей работе чистый clone с `dvc pull` восстановил файлы именно из `..\dvc-remote-storage`.

3. **Чем Dataset version отличается от Dataset ID в ClearML?**
   `version` — это человекочитаемая метка (`1.0.0`, `1.1.0`, `2.0.0`), может повторяться у разных датасетов. `Dataset ID` — уникальный UUID, однозначно идентифицирующий конкретную финализированную версию. Мы скачивали строго по ID, чтобы не зависеть от поиска по имени/версии.

4. **Почему `finalize()` нельзя считать созданием следующей версии?**
   `finalize()` только закрывает текущую версию, делая её immutable. Новая версия создаётся через `Dataset.create()` с указанием `parent_datasets`. В нашей работе `1.1.0` и `2.0.0` созданы отдельными вызовами `create()` с родителем `BASE_ID`.

5. **Как доказать, что ClearML version `2.0.0` создана от базы, а не от `1.1.0`?**
   В выводе скрипта: `Lineage: {'776a29a5...': ['b776397a...']}` — родитель только `BASE_ID`. Если бы родителем был `WINE_ID`, в lineage было бы `['b98b2f92...']`. Кроме того, в `2.0.0` нет `wine.csv`, который унаследовался бы от `1.1.0`.

6. **Что произойдёт, если после `git switch` не выполнить DVC checkout?**
   Workspace останется в состоянии предыдущей ветки: файлы CSV не будут соответствовать `data.dvc` новой ветки. В нашем случае после `git switch main` без `dvc checkout` остался бы `wine.csv` из `feature/wine`, хотя `main` его не содержит. `dvc status` показал бы расхождение, а `check_data.py` мог бы упасть или показать лишние файлы.

7. **В каком сценарии этой работы удобнее DVC, а в каком ClearML Dataset?**
   - **DVC** удобнее, когда версии данных жёстко связаны с Git-историей кода и нужно переключаться между ветками вместе с кодом (как в шагах 5–7). Merge driver автоматически объединяет данные при слиянии веток.
   - **ClearML Dataset** удобнее, когда нужен lineage-граф с ветвлением и независимыми версиями, доступными через веб-интерфейс без Git (шаги 10–12). Версии immutable, их можно скачивать по ID на любую машину, не клонируя репозиторий.



## Практика 4. Эксперименты и регистрация модели

### Подготовка данных

Для экспериментов использован финализированный датасет Wine из практики 3.

- **ClearML Dataset ID:** `b98b2f92d7ac4ac8a462cda305e6256c`
- **SHA-256:** `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60`
- **Разбиение:** стратифицированное, 60/20/20.
- **Количество объектов:** 178.
- **Train:** 106 объектов.
- **Validation:** 36 объектов.
- **Test:** 36 объектов.

Для всех запусков использовалось одинаковое разбиение данных. Тестовая выборка не применялась при выборе лучшей модели.

### Настройка MLflow

Для отслеживания экспериментов использован MLflow.

- **Tracking URI:** `sqlite:///C:/proga/ЩАС/MLUPS/experiments/practice_3/Aprelikova/mlops-data-Aprelikova/mlflow.db`
- **Experiment name:** `miit-mlops-practice-4-aprelikova`
- **Experiment ID:** `1`

Проведено шесть запусков: три с Logistic Regression и три с Random Forest. Для каждого запуска сохранялись параметры модели, метрики качества, время обучения и артефакт модели `model`.

### Сравнение экспериментов

Модели сравнивались по метрике weighted F1 на валидационной выборке. Время обучения указано в секундах.

| Модель | Параметры | Validation F1 | Время обучения |
|---|---|---:|---:|
| Logistic Regression | C = 1.0 | 0.943525 | 0.007434 |
| Logistic Regression | C = 0.1 | 0.943525 | 0.008874 |
| Logistic Regression | C = 10.0 | 0.914747 | 0.004956 |
| Random Forest | n_estimators = 100, max_depth = None | **0.972369** | 0.076671 |
| Random Forest | n_estimators = 200, max_depth = 5 | 0.944833 | 0.122115 |
| Random Forest | n_estimators = 200, max_depth = None | 0.944833 | 0.127617 |

### Выбор лучшей модели

Лучшей моделью по weighted F1 на валидационной выборке стала **Random Forest** со следующими параметрами:

- `n_estimators = 100`
- `max_depth = None`
- `min_samples_leaf = 1`
- `random_state = 42`

**Best MLflow Run ID:** `78d2c24d82d54e2082718b07ad334a07`

Validation F1: **0.972369**.

После выбора модели выполнена оценка на тестовой выборке:

| Метрика | Значение |
|---|---:|
| Accuracy | 0.944444 |
| Precision weighted | 0.944444 |
| Recall weighted | 0.944444 |
| F1 weighted | 0.944444 |

### Проверка модели

Лучшая модель повторно загружена из MLflow по URI:

`runs:/78d2c24d82d54e2082718b07ad334a07/model`

Проверки завершились успешно:

- MLflow signature присутствует.
- Предсказания загруженной модели совпадают с предсказаниями исходной модели.
- Обязательные параметры и метрики присутствуют.
- Проверка выполнена на исходных названиях признаков.

Результаты проверок сохранены в `practice_4/verification.json`.

### Регистрация в ClearML

Для лучшей модели создана задача ClearML:

- **Project:** `MIIT/MLOps/practice_4/Aprelikova`
- **Task name:** `wine-best-model`
- **Task ID:** `87a2e4b09ba04579be78ae4ce35310c2`

Модель зарегистрирована через `OutputModel` и опубликована после прохождения проверок.

- **Model name:** `wine-best-model`
- **ClearML Model ID:** `5c9f8f30698a45a1bd822e7b50039e74`

В задачу ClearML загружены модель, `comparison.csv` и `verification.json`. В метаданных модели сохранены MLflow Run ID, ClearML Dataset ID и SHA-256 датасета.

### Воспроизведение экспериментов

Основной скрипт экспериментов находится в `practice_4/run_experiments.py`. Он загружает датасет по ClearML Dataset ID, проверяет SHA-256, выполняет эксперименты, выбирает лучшую модель по валидационной метрике и оценивает её на тестовой выборке.

Результаты экспериментов сохраняются в MLflow, а проверка лучшей модели — в `verification.json`.