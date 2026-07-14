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
│   └── points[]
├── visits[]
├── red_flags[]
└── ai_summary
```

`metrics[]` — универсальная коллекция временных рядов. Экран выбирает ряд по
стабильному backend-коду (`glucose`, `hba1c`, `systolic`), а не ищет данные в
конкретном блоке JSON.

Модели находятся в `src/contracts/dashboard/v1/`. Как и канонический
контракт, они запрещают неизвестные поля и требуют новую major-версию при
несовместимом изменении.

Поля `red_flags` и `ai_summary` уже входят в стабильную форму ответа, но будут
заполняться отдельными сервисами на следующих этапах.
