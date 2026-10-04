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

Перед первым запуском выполните `searcher/scripts/perovskite_database_managment_postgres/init.sql` через `psql` от имени
администратора PostgreSQL (версия 15+). Скрипт создаёт отдельную базу `perovskites`,
пользователя `perovskites` с паролем `perovskites` и таблицы модели 2.1.
Скрипт самодостаточен: содержит создание всех девяти таблиц, индексов и ограничений
модели 2.1. Повторный запуск создаёт отсутствующие объекты без удаления данных;
существующий пароль не меняется. Это не миграция несовместимых старых схем.
По умолчанию пример использует
`postgresql://perovskites:perovskites@postgres.g:5432/perovskites`;
заданный `DATABASE_URL` имеет приоритет.
Параметры LLM берутся из обычной секции `[llm_chat]` конфигурационного файла.

```sh
psql -h postgres.g -U postgres -d postgres -X \
  -f searcher/scripts/perovskite_database_managment_postgres/init.sql

cd searcher
uv run python main.py -c conf/example.ini paper_to_perovskite paper.pdf
uv run python main.py -c conf/example.ini paper_to_perovskite paper1.pdf paper2.pdf
uv run python main.py -c conf/example.ini best_perovskite \
  "best lead-free material with the lowest reported band gap"
```

Несколько PDF обрабатываются последовательно, каждый в отдельном контексте агента.
Лимит `--max-characters` применяется к каждой статье. При исключении обработка
останавливается; ранее добавленные datasets остаются в базе.

Первый агент извлекает подтверждённые статьёй сведения, проверяет их через
Pydantic-модель 2.1 и добавляет один dataset. Второй преобразует запрос
пользователя в один или несколько поисков по поддерживаемым полям, сравнивает
найденные числовые свойства и возвращает `dataset_id` и ID материала.
