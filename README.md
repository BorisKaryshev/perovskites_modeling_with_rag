# Программный модуль моделирования перовскитов с применением технологии RAG для стабилизации нейронных сетей


# Эксперименты

## Эксп. 1. RAG vs plain generation

Отчеты:
- [Plain generation](./searcher/experimental_reports/2026_04_16-22_49_52/README.md)
- [RAG with embeddings only search](./searcher/experimental_reports/2026_04_17-17_40_36/README.md)
- [RAG with hybrid search](./searcher/experimental_reports/2026_04_16-23_29_21/README.md)

## Агенты для базы перовскитов

Python-инструменты `add_perovskite_structure`, `delete_perovskite_structure` и
`search_perovskite_structures` находятся в
`searcher/src/tools/perovskite_database.py`. Они используют актуальную модель
2.1, скопированную в `searcher/src/perovskite_models`, и PostgreSQL-схему
`searcher/sql/schema-v2.1.sql`. Каталог `searcher` содержит весь необходимый код;
внешний каталог или симлинк `perovskite_structure` не требуется.

Перед запуском примените схему к пустой базе. По умолчанию пример использует
`postgresql://localhost/perovskites`; заданный `DATABASE_URL` имеет приоритет.
Параметры LLM берутся из обычной секции `[llm_chat]` конфигурационного файла.

```sh
psql "${DATABASE_URL:-postgresql://localhost/perovskites}" \
  -X -v ON_ERROR_STOP=1 \
  -f searcher/sql/schema-v2.1.sql

cd searcher
uv run python main.py -c conf/example.ini paper_to_perovskite paper.pdf
uv run python main.py -c conf/example.ini best_perovskite \
  "best lead-free material with the lowest reported band gap"
```

Первый агент извлекает подтверждённые статьёй сведения, проверяет их через
Pydantic-модель 2.1 и добавляет один dataset. Второй преобразует запрос
пользователя в один или несколько поисков по поддерживаемым полям, сравнивает
найденные числовые свойства и возвращает `dataset_id` и ID материала.
