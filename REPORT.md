# Отчёт по практике 3. Версионирование данных с DVC и ClearML

## Версии данных

### Окружение

- Python: 3.12
- DVC: 3.67.1
- ClearML: 2.2.0
- scikit-learn: 1.9.1
- pandas: 3.1.1
- Git: 2.46.0.windows.1

Ссылка на Git-репозиторий: (указать после публикации)

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