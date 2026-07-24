= Пользовательская и разработческая документация

== Пользовательский сценарий

Пользователь запускает приложение из корня репозитория:

```bash
streamlit run src/app/main.py
```

Пользователь загружает JSON-файл либо создаёт синтетическую выгрузку по seed,
глубине истории и режиму. После обработки интерфейс показывает профиль,
заболевания, терапию, графики показателей и ленту приёмов. Сгенерированный
исходный JSON можно скачать. ИИ-сводка формируется только после нажатия кнопки.
Для сводки в локальном `.env` можно указать `GEMINI_API_KEY`; отсутствие ключа
не блокирует остальные функции. `OUTPUT_DIR` используется только при явном
сохранении через `MISParser.parse()` и не влияет на Streamlit. Секреты и
локальные результаты не сохраняются в Git.

== Документация разработчика

Разработчику доступны отдельные документы по generator, parser, контролю
качества, контракту данных, backend, frontend, summarizer и workflow.
Архитектурные диаграммы хранятся вместе с технической документацией в
`docs/diagrams` и повторно используются в этом отчёте. Источником истины при
расхождении являются Pydantic-контракты и тесты. Изменение публичного поведения
должно сопровождаться обновлением соответствующей документации.

Основные программные пакеты имеют направленные зависимости:

```text
src/generator    -> стандартная библиотека Python
src/quality      -> generator, parser, contracts/patient
src/parser       -> src/contracts/patient
src/parser       -> src/storage (только для parse)
src/storage      -> src/contracts/patient
src/calculators  -> примитивные типы
src/backend      -> contracts/patient, contracts/dashboard, calculators
src/summarizer   -> contracts/patient, contracts/dashboard,
                    contracts/summarizer, Gemini API
src/app          -> generator, parser, backend, summarizer и их контракты
```

Parser не импортирует backend или UI, а frontend не обращается к адаптерам
исходной МИС.

== Схема хранения данных

Отдельная реляционная база данных в прототипе отсутствует. Канонический документ
имеет следующую логическую схему:

```text
PatientRecord 1.0
├── schema_version = "1.0"
├── patient
├── social_history?
├── family_history[]
├── allergies[]
├── conditions[]
├── encounters[]
│   └── diagnoses[]
├── medications[]
├── observations[]
├── procedures[]
├── hospitalizations[]
├── immunizations[]
└── diagnostic_reports[]
```

Сохранение выполняется атомарно через временный файл с последующей заменой.
Загрузка включает JSON-декодирование и строгую валидацию `PatientRecord`.
Таким образом, файловое хранилище уже имеет явную границу, которую можно заменить
реализацией базы данных на следующем этапе.
