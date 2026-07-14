#import "project.typ": project
#import "styles.typ": slide-theme, slide

#show: slide-theme

#align(center + horizon)[
  #text(size: 18pt, fill: rgb("64748b"))[Технологический проект в рамках стажировки]
  #v(0.3in)
  #text(size: 40pt, weight: "bold", fill: rgb("075985"))[#project.short-title]
  #v(0.25in)
  #text(size: 22pt)[Дашборд-сводка по данным медицинской информационной системы]
  #v(0.65in)
  #text(size: 18pt)[#project.author]
  #v(0.15in)
  #text(size: 15pt, fill: rgb("64748b"))[#project.institution]
]
#align(center + bottom)[#text(size: 14pt)[#project.city, #project.year]]
#pagebreak()

#slide(
  [Проблема],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35in,
      [
        *Врач ограничен временем*

        Многолетняя карта содержит сотни событий, а на амбулаторный приём
        отведены минуты.
      ],
      [
        *Экспорт МИС неоднороден*

        Разные форматы дат и чисел, пропуски, опечатки, свободный текст и
        частичные дубли.
      ],
    )
    #v(0.45in)
    #block(fill: rgb("e0f2fe"), inset: 18pt, radius: 6pt)[
      *Задача:* показать врачу главное за 30 секунд, не скрывая происхождение
      данных и не подменяя медицинское решение.
    ]
  ],
  subtitle: [Почему исходный JSON нельзя напрямую передать интерфейсу],
)

#slide(
  [Цель и задачи],
  [
    *Цель:* преобразовать грязную выгрузку МИС в устойчивую структурированную
    модель и компактный веб-дашборд.

    #v(0.25in)
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35in,
      [
        - исследовать структуру данных;
        - нормализовать даты, числа и пропуски;
        - извлечь показатели из текста;
        - устранить явные дубли;
      ],
      [
        - сформировать backend-контракт;
        - реализовать калькуляторы и flags;
        - собрать Streamlit-интерфейс;
        - добавить проверяемую LLM-сводку.
      ],
    )
  ],
)

#slide(
  [Что находится во входных данных],
  [
    #grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 0.2in,
      [*Структурированное* \
       пациент, диагнозы, назначения, лабораторные панели],
      [*Свободный текст* \
       жалобы, осмотр, заключения ЭКГ, УЗИ и других исследований],
      [*Самоконтроль* \
       артериальное давление, пульс и глюкоза из дневника],
    )
    #v(0.45in)
    #block(fill: rgb("fff7ed"), stroke: rgb("f59e0b"), inset: 16pt, radius: 6pt)[
      `birtf_date`, `JALOBY_TXT`, `"46,5"`, Unix timestamp, `null`, `"-"`,
      отсутствующие разделы и legacy-дубли — ожидаемые варианты входа, а не
      исключительные аварии.
    ]
  ],
)

#slide(
  [Архитектура],
  [
    #align(center)[
      #grid(
        columns: (1fr, auto, 1fr, auto, 1fr),
        gutter: 0.12in,
        align: center + horizon,
        block(fill: rgb("e0f2fe"), inset: 14pt, radius: 5pt)[*Dirty JSON*],
        [→],
        block(fill: rgb("dbeafe"), inset: 14pt, radius: 5pt)[*MISParser*],
        [→],
        block(fill: rgb("dcfce7"), inset: 14pt, radius: 5pt)[*PatientRecord v1*],
      )
      #v(0.25in)
      #text(size: 30pt)[↓]
      #v(0.2in)
      #grid(
        columns: (1fr, auto, 1fr, auto, 1fr),
        gutter: 0.12in,
        align: center + horizon,
        block(fill: rgb("fef3c7"), inset: 14pt, radius: 5pt)[*Streamlit*],
        [←],
        block(fill: rgb("ffedd5"), inset: 14pt, radius: 5pt)[*DashboardResponse v1*],
        [←],
        block(fill: rgb("f3e8ff"), inset: 14pt, radius: 5pt)[*DashboardService*],
      )
    ]
    #v(0.35in)
    #align(center)[Frontend зависит от стабильного ответа backend, а не от полей МИС.]
  ],
)

#slide(
  [Ключевые методы],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35in,
      [
        *Tolerant reader*

        Безопасный доступ к структурам, псевдонимы полей, обработка отсутствующих
        блоков и явных пропусков.

        *Нормализация*

        Несколько форматов дат, Unix timestamp, числа с запятой, контроль
        `NaN` и бесконечностей.
      ],
      [
        *Извлечение из текста*

        Regex для АД и ЧСС с сохранением категории источника.

        *Strict contract*

        Pydantic-модели запрещают неизвестные выходные поля и фиксируют
        версию схемы.
      ],
    )
  ],
)

#slide(
  [Текущий результат],
  [
    #grid(
      columns: (1fr, 1fr, 1fr, 1fr),
      gutter: 0.15in,
      ..(
        ("20 268", "наблюдений"),
        ("81", "приём"),
        ("15", "временных рядов"),
        ("67", "автотестов"),
      ).map(((value, label)) => block(
        fill: white,
        stroke: rgb("cbd5e1"),
        inset: 14pt,
        radius: 6pt,
      )[
        #align(center)[
          #text(size: 31pt, weight: "bold", fill: rgb("075985"))[#value]
          #v(0.08in)
          #text(size: 14pt)[#label]
        ]
      ]),
    )
    #v(0.45in)
    #block(fill: rgb("ecfdf5"), inset: 16pt, radius: 6pt)[
      Готовы parser, `PatientRecord v1`, атомарное файловое хранение,
      `DashboardResponse v1` и backend-проекции профиля, метрик и приёмов.
    ]
  ],
  subtitle: [Проверка на эталонном синтетическом пациенте],
)

#slide(
  [Команда и личный вклад],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35in,
      [
        *Рамин Султангалиев*

        - требования к parser;
        - архитектура контрактов;
        - backend-проекции;
        - тесты, review и документация.
      ],
      [
        *#project.teammate*

        - Streamlit frontend;
        - визуализация контракта;
        - взаимное code review;
        - TODO: уточнить фактический вклад.
      ],
    )
    #v(0.35in)
    #text(size: 17pt, fill: rgb("475569"))[
      Codex использовался как инструмент разработки; ответственность за
      требования, решения и проверку результата оставалась у участников.
    ]
  ],
)

#slide(
  [Следующие этапы],
  [
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35in,
      [
        *До завершения MVP*

        1. Медицинские калькуляторы.
        2. Объяснимые red flags.
        3. Streamlit frontend.
        4. Структурированная LLM-сводка.
      ],
      [
        #block(
          fill: white,
          stroke: (paint: rgb("94a3b8"), dash: "dashed"),
          inset: 18pt,
          radius: 6pt,
          height: 2.3in,
        )[
          #align(center + horizon)[
            #text(size: 18pt, fill: rgb("64748b"))[
              TODO: скриншот готового dashboard
            ]
          ]
        ]
      ],
    )
  ],
  subtitle: [Главное ограничение текущей версии — пользовательский интерфейс ещё не интегрирован],
)

#slide(
  [Выводы],
  [
    - Главная сложность проекта — качество и семантика медицинских данных, а не
      построение графика.
    - Канонический контракт предотвращает раннюю потерю полезной информации.
    - Backend-driven подход позволяет независимо развивать parser и frontend.
    - Медицинские формулы требуют подтверждённых источников и тестов.
    - LLM используется для текста, но не для вычисления клинических показателей.

    #v(0.4in)
    #align(center)[
      #text(size: 28pt, weight: "bold", fill: rgb("075985"))[
        Цель — не заменить врача, а сократить время поиска главного.
      ]
    ]
  ],
)
