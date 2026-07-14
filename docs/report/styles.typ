#let report-style(body) = {
  set document(title: "Отчёт по проекту «Пациент за 30 секунд»")
  set page(
    paper: "a4",
    margin: (left: 30mm, right: 15mm, top: 20mm, bottom: 20mm),
    numbering: "1",
    number-align: center + bottom,
  )
  set text(font: "Liberation Serif", size: 14pt, lang: "ru")
  set par(justify: true, leading: 0.65em, first-line-indent: 1.25cm)
  set heading(numbering: "1.")
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    set text(size: 16pt, weight: "bold")
    set par(first-line-indent: 0pt)
    block(above: 1em, below: 0.8em)[#it]
  }
  show heading.where(level: 2): it => {
    set text(size: 14pt, weight: "bold")
    set par(first-line-indent: 0pt)
    block(above: 0.8em, below: 0.5em)[#it]
  }
  body
}

#let title-page(project) = {
  set page(numbering: none)
  set par(first-line-indent: 0pt, justify: false)

  align(center)[
    #text(size: 12pt, weight: "bold")[#project.institution]

    #v(0.5em)
    #text(size: 12pt)[#project.faculty]
  ]

  v(1fr)

  align(center)[
    #text(size: 16pt, weight: "bold")[#upper(project.report-kind)]

    #v(1.2em)
    #text(size: 18pt, weight: "bold")[«#project.title»]
  ]

  v(1fr)

  align(right)[
    #block(width: 90mm)[
      *Выполнил:* #project.author \
      *Направление:* #project.program \
      *Группа:* #project.group \
      *Место стажировки:* #project.internship-place \
      *Сроки:* #project.internship-dates

      #v(1em)
      *Руководитель от образовательной организации:* \
      #project.university-supervisor

      #v(1em)
      *Руководитель от организации:* \
      #project.internship-supervisor
    ]
  ]

  v(1fr)

  align(center)[#project.city \ #project.year]
  pagebreak()
  counter(page).update(1)
}

#let slide-theme(body) = {
  set document(title: "Презентация проекта «Пациент за 30 секунд»")
  set page(
    width: 13.333in,
    height: 7.5in,
    margin: (x: 0.65in, y: 0.45in),
    fill: rgb("f7f9fc"),
  )
  set text(font: "FreeSans", size: 24pt, fill: rgb("17243b"), lang: "ru")
  set par(leading: 0.65em)
  body
}

#let slide(title, body, subtitle: none) = {
  set page(header: context [
    #text(size: 11pt, fill: rgb("64748b"))[Пациент за 30 секунд]
    #h(1fr)
    #text(size: 11pt, fill: rgb("64748b"))[#counter(page).display()]
  ])
  text(size: 31pt, weight: "bold", fill: rgb("075985"))[#title]
  if subtitle != none {
    v(0.15in)
    text(size: 17pt, fill: rgb("64748b"))[#subtitle]
  }
  v(0.3in)
  body
  pagebreak(weak: true)
}
