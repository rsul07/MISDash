# Frontend handoff: быстрый Streamlit MVP с Codex

## 1. Цель задачи

Нужно максимально быстро собрать frontend «Пациент за 30 секунд» на Streamlit.
Frontend не читает исходные поля МИС и не разбирает `patient_record.json`
самостоятельно. Единственный источник данных для UI — `DashboardResponse v1`,
который возвращает `DashboardService`.

Минимальный готовый результат:

- загрузка JSON-файла пациента;
- шапка пациента: ФИО, возраст, пол, группа крови, ИМТ и вес;
- заметный блок аллергий;
- хронические состояния и текущая терапия;
- графики ключевых показателей;
- таблица врачебных приёмов;
- корректные пустые состояния для `red_flags` и `ai_summary`;
- понятная ошибка вместо падения на некорректном JSON;
- запуск одной командой;
- `pytest -q` остаётся зелёным.

Не входит в frontend-задачу:

- изменение parser, canonical adapters и backend-контрактов;
- вычисление медицинских формул или red flags в UI;
- вызов LLM;
- аутентификация, база данных и production deployment;
- сложная дизайн-система и ручная CSS-вёрстка.

Если для UI не хватает backend-поля, не извлекать его из сырого JSON. Описать
нехватку в PR и согласовать изменение `DashboardResponse` с backend-разработчиком.

## 2. Нужен ли merge backend перед началом

Технически нет: frontend-ветку можно создать от `feat/parser-backend`.
Практически для минимальной нагрузки рекомендуется сначала влить backend в
`main`, а затем создать frontend-ветку от обновлённого `main`.

Плюсы merge перед стартом:

- frontend PR содержит только frontend-изменения;
- не возникает зависимого/stacked PR;
- проще получать обновления команды;
- reviewer не видит backend diff повторно;
- после merge frontend не нужно менять base branch.

Использовать ветку от `feat/parser-backend` стоит только если merge задерживается,
а работу нужно начать немедленно. Оба сценария описаны ниже.

## 3. Подготовка компьютера до offline-работы

Все команды выполняются из терминала. Строки, начинающиеся с `#`, — комментарии,
их вводить не нужно.

### 3.1. Проверить инструменты

```bash
git --version
python --version
python -m pip --version
```

Нужен Python 3.10 или новее. Если используется команда `python3`, заменить
`python` на `python3` во всех командах ниже.

### 3.2. Клонировать репозиторий впервые

```bash
git clone git@github.com:rsul07/mis_dash.git
cd mis_dash
git status
```

Если SSH-доступ к GitHub не настроен, использовать HTTPS:

```bash
git clone https://github.com/rsul07/mis_dash.git
cd mis_dash
```

### 3.3. Создать виртуальное окружение

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

После активации путь `.venv` обычно появляется слева в строке терминала.
Перед каждой новой сессией терминала окружение нужно активировать снова.

### 3.4. Скачать зависимости для установки без интернета

Этот шаг выполнить, пока интернет доступен. Wheels хранить вне репозитория,
чтобы случайно не добавить их в Git.

Linux/macOS:

```bash
mkdir -p "$HOME/mis_dash_wheels"
python -m pip download -r requirements.txt -d "$HOME/mis_dash_wheels"
```

Offline-установка из сохранённого каталога:

```bash
python -m pip install --no-index \
  --find-links "$HOME/mis_dash_wheels" \
  -r requirements.txt
```

Wheels зависят от операционной системы и версии Python. Скачивать их нужно на
том же компьютере и с той же версией Python, где будет offline-разработка.

### 3.5. Создать `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Для frontend MVP достаточно:

```dotenv
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
DEBUG_MODE=True
OUTPUT_DIR=data/output_test/
```

`LLM_API_KEY` пока не используется, оставляется placeholder. Настоящий ключ не
добавлять в Git. `.env` уже игнорируется через `.gitignore`.

### 3.6. Проверить локальную среду

```bash
python -c "import streamlit, plotly, pandas, pydantic; print('dependencies ok')"
pytest -q
```

До начала frontend-задачи все backend-тесты должны проходить.

## 4. Git: рекомендуемый старт после merge backend

Сначала убедиться, что нет незакоммиченных файлов:

```bash
git status
```

Ожидаемая строка: `working tree clean`. Если есть изменения, не удалять их.
Сначала сделать отдельный commit или выполнить `git stash push -u`.

Получить свежий `main` и создать feature branch:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c feat/frontend-dashboard
git push -u origin feat/frontend-dashboard
```

Проверка:

```bash
git branch --show-current
git status -sb
```

Должна быть активна `feat/frontend-dashboard`, а не `main`.

Если локальная ветка уже существует:

```bash
git switch feat/frontend-dashboard
```

Если ветка существует только на GitHub:

```bash
git fetch origin
git switch --track origin/feat/frontend-dashboard
```

## 5. Git: старт до merge backend

Использовать только если ждать merge нельзя:

```bash
git fetch origin
git switch -c feat/frontend-dashboard origin/feat/parser-backend
git push -u origin feat/frontend-dashboard
```

PR frontend в этом случае временно открывается с base branch
`feat/parser-backend`, иначе GitHub покажет в нём весь backend. После merge
backend изменить base branch PR на `main` и проверить diff ещё раз.

Нельзя создавать frontend-ветку от старого локального `main` без `git fetch` и
`git pull`, иначе в ней не будет `DashboardService`.

## 6. Существующий API для frontend

Для локального файла:

```python
from src.backend import DashboardService
from src.parser import MISParser

record = MISParser("data/patient_etalon.json").parse_record()
dashboard = DashboardService().build(record)
```

Не использовать в UI:

- `src.parser.canonical.*`;
- исходные ключи `PATIENT_INFO`, `PRIEMY_VRACHA`, `JALOBY_TXT`;
- прямое чтение вложенностей `patient_record.json`;
- удалённые форматы `profile.json`, `vitals.csv`, `visits.csv`.

### 6.1. Поля `DashboardResponse`

```text
schema_version
generated_at
patient
allergies[]
conditions[]
current_medications[]
metrics[]
visits[]
red_flags[]
ai_summary
```

Модели находятся в `src/contracts/dashboard/v1/`. Перед написанием компонента
открыть соответствующую модель и использовать её поля, не угадывать схему.

### 6.2. Метрики

`dashboard.metrics` — список `MetricSeries`. У каждого ряда есть:

- `code` — стабильный машинный код;
- `display` — подпись для врача;
- `unit` — единица;
- `points` — `observed_at`, `value`, `source_category`, `encounter_id`.

Доступные коды:

```text
systolic
diastolic
heart-rate
body-weight
bmi
glucose
hba1c
creatinine
total-cholesterol
ldl-cholesterol
hdl-cholesterol
triglycerides
potassium
oxygen-saturation
body-temperature
```

Для быстрого поиска ряда:

```python
metrics = {series.code: series for series in dashboard.metrics}
glucose = metrics.get("glucose")
```

UI обязан корректно работать, если любого ряда нет.

## 7. Рекомендуемая структура frontend

Не создавать один огромный файл. Минимальная структура:

```text
src/app/
├── main.py
├── data.py
└── components/
    ├── __init__.py
    ├── patient.py
    ├── metrics.py
    └── visits.py
```

Ответственность:

- `main.py` — page config, uploader, композиция секций;
- `data.py` — bytes загруженного файла → `DashboardResponse`, cache и ошибки;
- `patient.py` — шапка, аллергии, диагнозы, терапия;
- `metrics.py` — выбор и отрисовка графиков;
- `visits.py` — таблица приёмов;
- red flags и AI summary можно показать компактно в `main.py`, пока они пусты.

Карточка пациента реализована публичной функцией
`render_patient_card(dashboard: DashboardResponse)` в
`src/app/components/patient.py`. Компонент получает только backend-проекцию,
показывает нейтральные состояния для отсутствующих значений и пустых списков и
не вычисляет медицинские показатели самостоятельно.

Графики реализованы функцией `render_metrics(dashboard: DashboardResponse)` в
`src/app/components/metrics.py`. Ряды выбираются по стабильным `code`, делятся
на клинические группы и дополнительно разводятся по отдельным графикам при
несовместимых единицах измерения. Пользователь переключает доступные группы
ленивыми вкладками `st.tabs(..., on_change="rerun")`: frontend строит Plotly-
фигуры только для активной вкладки и не исчерпывает лимит WebGL-контекстов
браузера. Для этого требуется Streamlit 1.59 или новее; разбор файла при
переключении не повторяется благодаря `st.cache_data`.

Плотные серии отображаются линиями без сплошного слоя маркеров и по умолчанию
открываются на последнем годе данных. Plotly-кнопки позволяют выбрать один год,
три года или всю историю. Разреженные серии сохраняют линии и маркеры.
Отсутствующие группы не создают пустых вкладок; если нет ни одной поддерживаемой
серии, компонент показывает единое нейтральное сообщение. Исходные наблюдения и
поля МИС компоненту неизвестны.

Таблица приёмов реализована функцией
`render_visits(dashboard: DashboardResponse)` и сохраняет порядок записей,
подготовленный backend: от новых к старым. Секции `red_flags` и `ai_summary`
только отображают значения стабильного ответа через `render_insights`; при
пустых значениях показывается «Пока нет данных». Frontend не рассчитывает
флаги и не обращается к LLM.

Не добавлять отдельный CSS-файл в первой версии. Сначала закончить рабочий UI
на стандартных компонентах Streamlit.

## 8. Загрузка файла в Streamlit

`MISParser` принимает путь. `st.file_uploader` возвращает bytes, поэтому в
`data.py` нужен контролируемый временный файл.

Ожидаемый интерфейс:

```python
def build_dashboard(file_bytes: bytes) -> DashboardResponse:
    ...
```

Правила реализации:

1. Кэшировать функцию через `st.cache_data`, иначе Streamlit будет повторно
   разбирать 20 000+ observations на каждое действие.
2. Внутри кэша записать bytes в `tempfile.NamedTemporaryFile` с `.json`.
3. В `try` вызвать `MISParser(temp_path).parse_record()` и
   `DashboardService().build(record)`.
4. Возвращать `model_dump(mode="json")`, поскольку dict удобно кэшируется.
5. В `finally` удалить временный файл.
6. После кэша восстановить тип через `DashboardResponse.model_validate()`.
7. `ValueError`, `ValidationError` и `OSError` показать через `st.error`, а не
   через traceback пользователю.

В dev-режиме, если файл не загружен, разрешено показывать кнопку загрузки
эталона `data/patient_etalon.json`. Не читать эталон автоматически при каждом
rerun.

## 9. Порядок реализации с Codex

Официальная рекомендация Codex для сложной задачи: задать Goal, Context,
Constraints и Done when; сначала использовать Plan mode, после реализации
запустить проверки и review. Не отправлять prompt «сделай красивый frontend».

### 9.1. Первый prompt: только изучение и план

Открыть репозиторий в IDE, Codex — в корне `mis_dash`, затем включить `/plan` и
отправить:

```text
Прочитай полностью docs/frontend_handoff.md, docs/backend.md,
docs/data_contract.md, docs/workflow.md и docs/ts.md. Изучи модели
src/contracts/dashboard/v1 и публичный API DashboardService.

Цель: спланировать минимальный Streamlit frontend по frontend_handoff.md.
Сейчас ничего не изменяй. Проверь существующую структуру и тесты, задай только
вопросы, которые нельзя выяснить из репозитория. План раздели на небольшие
коммиты. Frontend не должен читать сырой JSON или canonical adapters.
```

Не разрешать реализацию, пока план не совпадает с разделами 1, 7 и 8 этого
документа.

### 9.2. Prompt 1: data boundary и каркас

Переключить Codex из Plan mode в обычный режим:

```text
Реализуй только первый шаг утверждённого плана: src/app/data.py и минимальный
src/app/main.py с file uploader. Используй MISParser.parse_record() и
DashboardService.build(), добавь cache и обработку ошибок по
docs/frontend_handoff.md. Не делай графики и визуальный polish. Добавь тесты
для data boundary, обнови документацию, запусти pytest. Сделай один атомарный
commit после успешной проверки.
```

Проверить самостоятельно:

```bash
git show --stat --oneline HEAD
pytest -q
streamlit run src/app/main.py
```

### 9.3. Prompt 2: карточка пациента

```text
Добавь только компонент карточки пациента в src/app/components/patient.py:
ФИО, возраст, пол, группа крови, BMI, вес, аллергии, хронические состояния и
текущая терапия. Используй только DashboardResponse. Обработай None и пустые
списки. Подключи компонент в main.py, добавь тесты, обнови frontend-документацию,
запусти pytest и сделай отдельный commit.
```

### 9.4. Prompt 3: графики

```text
Добавь компонент метрик. Используй dashboard.metrics и стабильные code, не
хардкодь расположение исходных данных. Покажи отдельные группы: АД/пульс,
диабет, почки, липиды, вес/BMI. Если ряда нет, UI не падает. Используй Plotly,
не добавляй новую dependency. Проверь производительность на эталоне, добавь
тесты, обнови docs, запусти pytest и сделай отдельный commit.
```

### 9.5. Prompt 4: визиты и пустые секции

```text
Добавь таблицу visits от новых к старым. Покажи дату, врача, специальность,
основной диагноз и жалобы. Добавь секции red_flags и ai_summary: отображай
данные, когда они есть, иначе нейтральное сообщение «Пока нет данных».
Frontend не вычисляет flags и не вызывает LLM. Добавь тесты, обнови docs,
запусти pytest и сделай отдельный commit.
```

### 9.6. Prompt 5: финальная проверка, без новых функций

```text
Не добавляй новых функций. Проведи финальный аудит frontend относительно
docs/frontend_handoff.md и docs/ts.md. Запусти все тесты, проверь imports,
обработку пустых данных и invalid JSON, размер файлов и git diff. Исправь только
найденные дефекты. Обнови README точной командой запуска. Затем выполни review
изменений относительно main и перечисли известные ограничения.
```

После этого запустить `/review` и выбрать review текущей ветки относительно
`main`. Codex не должен автоматически merge или удалять ветку.

## 10. Что проверять после каждого шага

Codex ускоряет работу, но разработчик принимает результат. После каждого
commit выполнить:

```bash
git status
git show --stat --oneline HEAD
pytest -q
```

Для UI также:

```bash
streamlit run src/app/main.py
```

Открыть адрес из терминала, обычно `http://localhost:8501`.

Ручная проверка:

1. Загрузить `data/patient_etalon.json`.
2. Убедиться, что показано имя пациента и нет traceback.
3. Переключить все доступные вкладки графиков и убедиться, что белые фигуры не
   появляются.
4. Проверить интервалы `1 год`, `3 года`, `Всё` и tooltip с датой и значением.
5. Проверить таблицу из 81 приёма.
6. Загрузить файл `{}` — UI должен показать пустые данные без падения.
7. Загрузить файл с текстом вместо JSON — UI должен показать понятную ошибку.
8. Перезагрузить страницу — приложение должно продолжить работу.

## 11. Коммиты и синхронизация ветки

Рекомендуемые commits:

```text
feat: add streamlit data loading flow
feat: add patient summary components
feat: add clinical metric charts
feat: add visit timeline and empty states
docs: document frontend launch and limitations
```

Перед каждым commit:

```bash
git status --short
git diff --check
pytest -q
```

Добавлять только относящиеся к шагу файлы:

```bash
git add src/app tests README.md docs
git commit -m "feat: add patient summary components"
git push
```

Если `main` обновился во время работы:

```bash
git fetch origin
git switch feat/frontend-dashboard
git merge origin/main
pytest -q
git push
```

При конфликте не выбирать blindly `ours` или `theirs`. Открыть конфликтующие
файлы, понять обе версии, исправить маркеры `<<<<<<<`, `=======`, `>>>>>>>`,
запустить тесты и только затем завершить merge commit.

## 12. Создание frontend PR

Перед PR:

```bash
git status
pytest -q
git diff --check
git log --oneline main..HEAD
git diff --stat main...HEAD
git push
```

PR:

- base: `main`;
- compare/head: `feat/frontend-dashboard`;
- title: `feat: add patient dashboard frontend`;
- назначить второго участника reviewer;
- не merge до зелёных тестов и ручной проверки эталона.

Описание PR должно содержать:

```markdown
## Что сделано
- загрузка JSON пациента;
- карточка пациента;
- клинические графики;
- таблица приёмов;
- состояния для flags и AI summary.

## Как проверить
1. `python -m pip install -r requirements.txt`
2. `pytest -q`
3. `streamlit run src/app/main.py`
4. загрузить `data/patient_etalon.json`

## Архитектурная граница
UI использует только `DashboardResponse v1`.

## Ограничения
- red flags пока приходят пустыми;
- AI summary пока отсутствует;
- production deployment не настроен.
```

## 13. Быстрое восстановление после ошибки Git

Посмотреть состояние и последние commits:

```bash
git status
git log --oneline --decorate -10
git branch -vv
```

Если изменения сделаны на `main`, но ещё не закоммичены:

```bash
git switch -c feat/frontend-dashboard
```

Если нужно временно убрать незавершённую работу:

```bash
git stash push -u -m "wip frontend"
git switch main
# чтобы вернуть позже:
git switch feat/frontend-dashboard
git stash pop
```

Не выполнять `git reset --hard`, `git clean -fd` и force push без согласования —
эти команды могут необратимо удалить работу.

## 14. Definition of Done frontend MVP

- [ ] Работа ведётся в `feat/frontend-dashboard`, не в `main`.
- [ ] `.env` создан локально и не попал в Git.
- [ ] `streamlit run src/app/main.py` запускает приложение.
- [ ] Эталонный JSON отображает профиль, метрики и 81 приём.
- [ ] Вкладки метрик лениво отображают только выбранную клиническую группу.
- [ ] UI не импортирует canonical parser adapters.
- [ ] Отсутствующие metric series и пустые списки не вызывают ошибок.
- [ ] Невалидный JSON показывает понятное сообщение.
- [ ] Red flags и AI summary имеют пустые состояния.
- [ ] `pytest -q` проходит.
- [ ] README содержит актуальную команду запуска.
- [ ] Изменения разделены на небольшие commits.
- [ ] PR открыт в `main`, назначен reviewer, заполнены шаги проверки.

## 15. Основные документы

Перед работой прочитать:

1. [Backend service](backend.md) — готовая frontend-проекция.
2. [Контракт данных](data_contract.md) — границы canonical/backend.
3. [Parser](parser.md) — откуда появляется `PatientRecord`.
4. [Workflow](workflow.md) — ветки, commits, PR и документация.
5. [Техническое задание](ts.md) — продуктовый результат.

По работе с Codex: официальный подход — давать Goal, Context, Constraints и
Done when, использовать Plan mode для сложных задач и `/review` перед приёмкой.
