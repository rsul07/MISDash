# 🩺 mis_dash

`mis_dash` — это прототип веб-дашборда, предназначенный для помощи врачам при работе с объемными электронными медицинскими картами (ЭМК). 

В реальной практике врач тратит драгоценное время приема на поиск нужной информации в истории болезни за 5-10 лет. Наша цель — создать инструмент, который берет на вход "грязную" JSON-выгрузку из Медицинской Информационной Системы (МИС) и за секунды формирует наглядную сводку: графики, "красные флаги" и резюме, сгенерированное ИИ.

## Cтек
- **Язык:** Python 3.10+
- **Интерфейс:** Streamlit
- **Анализ данных:** Pydantic / Pandas / regex
- **Тестирование:** Pytest
- **Интеграция:** LLM API для суммаризации

## Структура репозитория

- `/docs` — документация: ТЗ, описание структуры исходного JSON, схемы архитектуры.
- `/data` — директория для хранения выгрузок JSON (не эталонные игнорируются Git).
- `/tests` — юнит-тесты для проверки парсеров и медицинских формул.
- `/src` — исходный код (парсер, калькуляторы, дашборд, модуль LLM).
    - `parser/` — подготовка и очистка исходных данных.
    - `contracts/` — версионированные backend-модели данных.
    - `storage/` — чтение и атомарная запись канонических контрактов.
    - `backend/` — frontend-проекции из `PatientRecord`.
    - `calculators/` — медицинские формулы и проверки.
    - `summarizer/` — работа с LLM для текста.
    - `app/` — веб-слой дашборда.

## Документация

- [Техническое задание](docs/ts.md)
- [Регламент командной работы](docs/workflow.md)
- [Архитектура и работа модуля parser](docs/parser.md)
- [Backend-driven контракт данных](docs/data_contract.md)
- [Backend service и DashboardResponse v1](docs/backend.md)
- [Frontend handoff: Streamlit MVP с Codex](docs/frontend_handoff.md)

## Быстрый старт

1. Склонируйте репозиторий:

   ```bash
   git clone https://github.com/rsul07/mis_dash.git
   cd mis_dash
   ```

2. Создайте виртуальное окружение и активируйте его:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Подготовьте переменные окружения:

   ```bash
   cp .env.example .env
   ```

   Затем заполните переменные локально в `.env` — реальные значения ключей в репозиторий не коммитятся.

5. Проверьте тесты:

   ```bash
   pytest -q
   ```

6. После активации виртуального окружения запустите frontend из корня
   репозитория точной командой:

   ```bash
   streamlit run src/app/main.py
   ```

   Дополнительно задавать `PYTHONPATH` не требуется.
   Откройте показанный Streamlit адрес и загрузите `data/patient_etalon.json`.
   Веб-слой передает загруженный файл публичным фасадам `MISParser` и
   `DashboardService` и отображает только `DashboardResponse v1`; исходные поля
   МИС и canonical adapters во frontend не используются.

Графики динамики разделены на клинические вкладки. Streamlit лениво строит
только выбранную группу, чтобы не превышать браузерный лимит WebGL-контекстов.
Для плотных рядов по умолчанию показан последний год; кнопки над графиком
переключают интервалы `1 год`, `3 года` и `Всё`.

### Ограничения frontend MVP

- `red_flags` и `ai_summary` отображаются, но текущий backend их пока не
  заполняет;
- расчётная СКФ отсутствует в `DashboardResponse v1` и не вычисляется во
  frontend;
- аутентификация, production deployment и вызов LLM не входят в MVP;
- в репозитории доступен только `data/patient_etalon.json`, поэтому ручная
  проверка второго сгенерированного файла требует отдельной выгрузки.

## Парсер

```python
from src.parser import MISParser

record = MISParser("data/patient_etalon.json").parse_record()
```

Parser возвращает единственный канонический контракт `PatientRecord`. Для
сохранения в `patient_record.json` используйте `parse()` вместо
`parse_record()`.

Backend-проекция для frontend строится только из канонического контракта:

```python
from src.backend import DashboardService

dashboard = DashboardService().build(record)
payload = dashboard.model_dump(mode="json")
```
