#import "project.typ": project
#import "styles.typ": report-style, title-page

#show: report-style

#title-page(project)

#outline(title: [Содержание], indent: auto)
#pagebreak()

= Введение

Настоящий отчёт описывает технологический проект «#project.short-title»,
выполняемый в рамках стажировки. Проект посвящён обработке неоднородных данных
медицинской информационной системы и формированию компактной сводки, которую
врач может изучить перед приёмом пациента.

#v(1em)
#align(center)[
  #text(fill: rgb("b45309"), weight: "bold")[
    Начальная версия: разделы отчёта будут подключены следующими коммитами.
  ]
]
