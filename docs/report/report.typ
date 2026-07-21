#import "project.typ": project
#import "styles.typ": report-style, title-page

#show: report-style

#title-page(project)

#outline(title: [Содержание], indent: auto)
#pagebreak()

#heading(level: 1, numbering: none)[Введение]

Настоящий отчёт описывает технологический проект «#project.short-title»,
выполняемый в рамках стажировки. Проект посвящён обработке неоднородных данных
медицинской информационной системы и формированию компактной сводки, которую
врач может изучить перед приёмом пациента.

Исходные данные проекта синтетические и не содержат персональных данных, однако
их структура воспроизводит характерные проблемы реальных выгрузок: неполные
блоки, неодинаковые форматы дат и чисел, опечатки в именах полей, свободный
медицинский текст и дублирующиеся записи. Поэтому основное внимание уделено не
визуальному представлению одного файла, а построению устойчивого конвейера
преобразования данных.

#include "sections/01-problem.typ"
#include "sections/02-goals.typ"
#include "sections/03-stack.typ"
#include "sections/04-foundations.typ"
#include "sections/05-team.typ"
#include "sections/06-contribution.typ"
#include "sections/07-documentation.typ"
#include "sections/08-career.typ"
#include "sections/09-conclusion.typ"

#bibliography("references.bib", title: "Список использованных источников")
