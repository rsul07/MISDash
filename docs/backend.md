# Backend service и `DashboardResponse v1`

## Назначение

Backend service строит готовое представление дашборда из канонического
`PatientRecord`. Frontend зависит только от `DashboardResponse v1` и не знает:

- исходные имена и вложенность полей МИС;
- правила выбора актуального веса и терапии;
- как лабораторные компоненты превращаются в временные ряды;
- правила сортировки и фильтрации приёмов.

## Контракт ответа

```text
DashboardResponse v1
├── schema_version
├── generated_at
├── patient
├── allergies[]
├── conditions[]
├── current_medications[]
├── metrics[]
│   ├── calculation?
│   └── points[]
│       ├── source_ids[]
│       ├── calculation_inputs[]
│       └── interpretation?
├── visits[]
├── red_flags[]
└── ai_summary
```

`metrics[]` — универсальная коллекция временных рядов. Экран выбирает ряд по
стабильному backend-коду (`glucose`, `hba1c`, `systolic`), а не ищет данные в
конкретном блоке JSON.

У производного ряда поле `calculation` объясняет показатель, входы, назначение,
метод, стандарт и ограничения. Каждая производная точка помечена
`source_category="calculated"`, а `source_ids` содержит идентификаторы
канонических наблюдений, использованных в формуле. Обычная точка также содержит
ID исходного `Observation`.
Поле `calculation_inputs` производной точки содержит конкретные операнды,
единицы и ID источников. Оно позволяет frontend показать проверяемый пример
расчёта, не восстанавливая медицинскую формулу по исходному JSON.
Для eGFR и отношения альбумин/креатинин поле `interpretation` содержит категорию
KDIGO (`G*` или `A*`), вычисленную по неокруглённому значению. Это категория
точки, а не диагноз хронической болезни почек.

Модели находятся в `src/contracts/dashboard/v1/`. Как и канонический
контракт, они запрещают неизвестные поля и требуют новую major-версию при
несовместимом изменении.

Текущая minor-версия корневой схемы `DashboardResponse` — `1.1`. Каталог `v1`
обозначает совместимую major-линию, а не фиксирует minor-номер. Версия `1.1`
добавила необязательную трассировку расчётных точек; `PatientRecord` остаётся
на версии `1.0`, потому что его форма не менялась.

Поля `red_flags` и `ai_summary` уже входят в стабильную форму ответа.
`DashboardService` пока оставляет их пустыми: правила красных флагов будут
подключены отдельным модулем, а проверенный результат `SummaryService`
приложение добавляет в `ai_summary` без изменения контракта v1.

## Проекция профиля

`src/backend/profile.py` формирует шапку пациента. Возраст рассчитывается на
переданную сервису дату, вес/рост/ИМТ берутся из последних наблюдений с
резервом на демографические данные. Если готового ИМТ нет, backend вычисляет
его из актуальных роста и веса.

Текущей терапией считается список назначений из последнего по дате приёма,
где присутствуют связанные `medication_ids`.

## Лента приёмов

`src/backend/visits.py` возвращает приёмы от новых к старым и сохраняет только
стабильные поля ответа: врача, специальность, тип, диагнозы и жалобы.
Исходные поля `VRACH`, `diagnoz_priema` и `JALOBY_TXT` этому слою неизвестны.

## Временные ряды

`src/backend/metrics.py` преобразует scalar observations и компоненты АД в
универсальные `MetricSeries`. Backend публикует ограниченный словарь стабильных
кодов, среди которых:

- `systolic`, `diastolic`, `heart-rate`, `body-weight`, `bmi`;
- `glucose`, `hba1c`, `creatinine`, `potassium`;
- `total-cholesterol`, `ldl-cholesterol`, `hdl-cholesterol`, `triglycerides`;
- `urine-albumin-creatinine-ratio`.

`src/backend/calculations/` связывает канонические записи с чистыми формулами
из `src/calculators` и публикует дополнительные ряды:

- `egfr-ckd-epi-2021`;
- `non-hdl-cholesterol`;
- `calculated-ldl-cholesterol`, только если в панели нет пригодного прямого ЛПНП;
- `pulse-pressure`.

Липиды соединяются только внутри одного `report_id`, САД и ДАД — только внутри
одного `Observation`, а возраст для eGFR определяется на дату креатинина.
Производные значения не записываются обратно в `PatientRecord` и могут быть
полностью перестроены.

Русские и международные обозначения единиц нормализуются. Значение с
неизвестной или несовместимой единицей не подмешивается в ряд без доказанной
формулы конверсии.
Глюкоза и креатинин мочи не классифицируются как показатели крови. Точки
остаются отдельными и сортируются по времени; канонический слой не изменяется.

## Фасад сервиса

`DashboardService` — единственная точка композиции frontend-ответа:

```python
from src.backend import DashboardService

response = DashboardService().build_from_path(
    "data/output_test/patient_record.json"
)
payload = response.model_dump(mode="json")
```

```mermaid
flowchart LR
    JSON[patient_record.json] --> Repository[src/storage]
    Repository --> Record[PatientRecord v1]
    Record --> Service[DashboardService]
    Record --> Calculators[calculations + calculators]
    Service --> Profile[profile.py]
    Service --> Metrics[metrics.py]
    Service --> Visits[visits.py]
    Calculators --> Metrics
    Profile --> Response[DashboardResponse v1]
    Metrics --> Response
    Visits --> Response
    Response --> Frontend
```

`src/storage/patient_records.py` отвечает только за чтение, строгую валидацию
и атомарную запись канонического JSON. Проекции получают Pydantic-модель и не
зависят от файловой системы.
`generated_at` и дата расчёта возраста могут передаваться явно, что делает
сервис детерминированным в тестах.
