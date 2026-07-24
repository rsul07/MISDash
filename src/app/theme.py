"""Presentation-ready visual system for the Streamlit application."""

from __future__ import annotations

from html import escape

import streamlit as st


NAVY = "#0B2D4F"
INK = "#082A4C"
BLUE = "#168CCA"
TEAL = "#10A889"
ACTION_TEAL = "#087B68"
AMBER = "#D48817"
CRITICAL = "#B4233C"
BACKGROUND = "#F3F8FB"
SURFACE = "#FFFFFF"
BORDER = "#D5E3EA"
MUTED = "#536E84"


def apply_app_theme() -> None:
    """Inject the shared CSS layer once per Streamlit rerun."""

    st.markdown(f"<style>{_APP_CSS}</style>", unsafe_allow_html=True)


def render_app_header() -> None:
    """Render a compact product header aligned with the presentation style."""

    st.markdown(
        """
        <header class="mis-app-header mis-enter">
          <div>
            <div class="mis-eyebrow">КЛИНИЧЕСКАЯ СВОДКА</div>
            <h1>MIS Dash</h1>
            <p>Главное в истории пациента — в одном проверяемом представлении.</p>
          </div>
          <div class="mis-app-mark" aria-hidden="true">
            <span></span><span></span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_header() -> None:
    """Render the data-source heading in the dark navigation surface."""

    st.markdown(
        """
        <div class="mis-sidebar-brand">
          <div class="mis-sidebar-logo">M</div>
          <div>
            <strong>MIS Dash</strong>
            <span>Демонстрационный контур</span>
          </div>
        </div>
        <div class="mis-sidebar-section">ИСТОЧНИК ДАННЫХ</div>
        """,
        unsafe_allow_html=True,
    )


def render_source_status(*, filename: str, origin: str) -> None:
    """Show a quiet provenance badge instead of a full success alert."""

    source = "синтетическая выгрузка" if origin == "generated" else "загруженный JSON"
    st.markdown(
        (
            '<div class="mis-source-status mis-enter">'
            '<span class="mis-source-dot"></span>'
            f"<strong>{escape(filename)}</strong>"
            f"<span>{escape(source)} · данные обработаны</span>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    """Explain the first action without filling the main presentation frame."""

    st.markdown(
        """
        <section class="mis-empty-state mis-enter">
          <div class="mis-empty-icon" aria-hidden="true"></div>
          <div class="mis-eyebrow">НАЧАЛО РАБОТЫ</div>
          <h2>Откройте историю пациента</h2>
          <p>
            Загрузите JSON из МИС или создайте воспроизводимую синтетическую
            выгрузку в панели слева.
          </p>
          <div class="mis-empty-steps">
            <span><b>1</b> Выберите источник</span>
            <span><b>2</b> Обработайте историю</span>
            <span><b>3</b> Изучите сигналы и динамику</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(
    title: str,
    *,
    eyebrow: str,
    description: str | None = None,
) -> None:
    """Render consistent hierarchy for dashboard sections."""

    paragraph = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        (
            '<div class="mis-section-heading mis-enter">'
            f'<div class="mis-eyebrow">{escape(eyebrow)}</div>'
            f"<h2>{escape(title)}</h2>"
            f"{paragraph}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


_APP_CSS = f"""
:root {{
  --mis-navy: {NAVY};
  --mis-ink: {INK};
  --mis-blue: {BLUE};
  --mis-teal: {TEAL};
  --mis-action: {ACTION_TEAL};
  --mis-amber: {AMBER};
  --mis-critical: {CRITICAL};
  --mis-bg: {BACKGROUND};
  --mis-surface: {SURFACE};
  --mis-border: {BORDER};
  --mis-muted: {MUTED};
  --mis-shadow: 0 0.25rem 1.125rem rgba(8, 42, 76, 0.07);
}}

html, body, [class*="css"] {{
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}}

[data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(circle at 84% -8%, rgba(22, 140, 202, 0.08), transparent 28rem),
    var(--mis-bg);
}}

[data-testid="stMainBlockContainer"] {{
  max-width: 82rem;
  padding-top: 3.25rem;
  padding-bottom: 4rem;
}}

[data-testid="stHeader"] {{
  background: rgba(243, 248, 251, 0.88);
  backdrop-filter: blur(0.75rem);
}}

[data-testid="stSidebar"] {{
  background: var(--mis-navy);
  border-right: 0;
}}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  padding-top: 1.2rem;
  overflow-x: hidden !important;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
  color: #f6fbff;
}}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
  color: #b9cfdf;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] > label {{
  display: none;
}}

[data-testid="stSidebar"] [data-baseweb="radio"] {{
  width: 100%;
  min-width: 0;
  background: rgba(255, 255, 255, 0.07);
  border-radius: 0.75rem;
  padding: 0.55rem 0.65rem;
  margin-bottom: 0.35rem;
}}

[data-testid="stSidebar"] [data-baseweb="radio"] > div:last-child {{
  min-width: 0;
  white-space: normal;
  overflow-wrap: anywhere;
}}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.25);
}}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {{
  color: #d9e8f1;
}}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
  background: #ffffff;
  border-color: var(--mis-border);
}}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button span,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button svg {{
  color: var(--mis-navy) !important;
}}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {{
  background: #e8f4f2;
  border-color: var(--mis-teal);
}}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover span,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover svg {{
  color: var(--mis-action) !important;
}}

[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {{
  background: var(--mis-action);
  border-color: var(--mis-action);
}}

[data-testid="stSidebar"] [data-testid="stDownloadButton"] button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button p,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button span,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button svg {{
  color: #ffffff !important;
}}

[data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {{
  background: var(--mis-teal);
  border-color: var(--mis-teal);
}}

[data-testid="stSidebar"] [data-testid="stDownloadButton"] button:disabled {{
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  opacity: 0.65;
}}

[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] span,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] svg {{
  color: #ffffff !important;
}}

.mis-sidebar-brand {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0.25rem 0 1.75rem;
}}

.mis-sidebar-logo {{
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  background: linear-gradient(145deg, var(--mis-teal), var(--mis-blue));
  color: white;
  font-size: 1.15rem;
  font-weight: 800;
  box-shadow: 0 0.5rem 1.4rem rgba(16, 168, 137, 0.22);
}}

.mis-sidebar-brand strong,
.mis-sidebar-brand span {{
  display: block;
}}

.mis-sidebar-brand strong {{
  color: white;
  font-size: 1rem;
}}

.mis-sidebar-brand span {{
  color: #b9cfdf;
  font-size: 0.75rem;
  margin-top: 0.08rem;
}}

.mis-sidebar-section {{
  color: #7fcfc0;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin-bottom: 0.6rem;
}}

.mis-app-header {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-top: 1rem;
  padding-bottom: 1.35rem;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid var(--mis-border);
}}

.mis-app-header h1 {{
  color: var(--mis-ink);
  font-size: clamp(2rem, 4vw, 3.15rem);
  line-height: 1;
  letter-spacing: -0.04em;
  margin: 0.2rem 0 0.5rem;
}}

.mis-app-header p {{
  color: var(--mis-muted);
  font-size: 1rem;
  margin: 0;
}}

.mis-app-mark {{
  position: relative;
  width: 3rem;
  height: 3rem;
  border-radius: 1rem;
  background: var(--mis-navy);
  box-shadow: var(--mis-shadow);
}}

.mis-app-mark span {{
  position: absolute;
  display: block;
  background: var(--mis-teal);
  border-radius: 1rem;
}}

.mis-app-mark span:first-child {{
  width: 1.6rem;
  height: 0.34rem;
  left: 0.7rem;
  top: 1.33rem;
}}

.mis-app-mark span:last-child {{
  width: 0.34rem;
  height: 1.6rem;
  left: 1.33rem;
  top: 0.7rem;
}}

.mis-eyebrow {{
  color: var(--mis-action);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}}

.mis-source-status {{
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--mis-muted);
  font-size: 0.78rem;
  margin: 0.75rem 0 1rem;
}}

.mis-source-status strong {{
  color: var(--mis-ink);
}}

.mis-source-dot {{
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--mis-teal);
  box-shadow: 0 0 0 0.25rem rgba(16, 168, 137, 0.12);
}}

.mis-empty-state {{
  max-width: 48rem;
  margin: 5rem auto 0;
  padding: 3.5rem;
  text-align: center;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--mis-border);
  border-radius: 1.25rem;
  box-shadow: var(--mis-shadow);
}}

.mis-empty-icon {{
  position: relative;
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  margin: 0 auto 1.25rem;
  border-radius: 1rem;
  background: var(--mis-navy);
  color: var(--mis-teal);
  font-size: 2rem;
}}

.mis-empty-icon::before,
.mis-empty-icon::after {{
  content: "";
  position: absolute;
  display: block;
  border-radius: 999px;
  background: var(--mis-teal);
}}

.mis-empty-icon::before {{
  width: 1.35rem;
  height: 0.22rem;
}}

.mis-empty-icon::after {{
  width: 0.22rem;
  height: 1.35rem;
}}

.mis-empty-state h2 {{
  color: var(--mis-ink);
  font-size: 2rem;
  margin: 0.4rem 0 0.65rem;
}}

.mis-empty-state > p {{
  color: var(--mis-muted);
  max-width: 38rem;
  margin: 0 auto;
}}

.mis-empty-steps {{
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.6rem;
}}

.mis-empty-steps span {{
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  background: #eef5f8;
  color: var(--mis-muted);
  font-size: 0.78rem;
}}

.mis-empty-steps b {{
  color: var(--mis-action);
  margin-right: 0.2rem;
}}

.mis-section-heading {{
  margin: 1.25rem 0 1rem;
}}

.mis-section-heading h2 {{
  color: var(--mis-ink);
  font-size: clamp(1.55rem, 2.3vw, 2rem);
  letter-spacing: -0.025em;
  margin: 0.2rem 0 0.2rem;
}}

.mis-section-heading p {{
  color: var(--mis-muted);
  margin: 0;
}}

.mis-patient-heading {{
  padding: 0.2rem 0.35rem 0.2rem 0;
}}

.mis-patient-heading h2 {{
  color: var(--mis-ink);
  font-size: clamp(1.25rem, 2vw, 1.7rem);
  letter-spacing: -0.035em;
  line-height: 1.15;
  margin: 0.2rem 0 0;
}}

.mis-patient-id {{
  color: var(--mis-action);
  font-family: ui-monospace, "Cascadia Code", monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}}

.mis-patient-stat {{
  min-height: 5.8rem;
  padding: 0.75rem 0.7rem;
  border-radius: 0.8rem;
  background: #f7fafc;
  border: 1px solid #e2edf2;
}}

.mis-patient-stat span,
.mis-patient-stat strong {{
  display: block;
}}

.mis-patient-stat span {{
  min-height: 1.15rem;
  color: var(--mis-muted);
  font-size: 0.7rem;
  line-height: 1.2;
}}

.mis-patient-stat strong {{
  color: var(--mis-ink);
  font-size: clamp(1.05rem, 1.7vw, 1.45rem);
  line-height: 1.15;
  margin-top: 0.4rem;
  overflow-wrap: anywhere;
}}

.mis-clinical-panel {{
  min-height: 13rem;
  max-height: 19rem;
  margin-top: 1rem;
  padding: 0.95rem;
  overflow: hidden;
  border: 1px solid #e1ebf0;
  border-radius: 0.85rem;
  background: #f8fbfc;
}}

.mis-clinical-title {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid #e1ebf0;
}}

.mis-clinical-title h3 {{
  color: var(--mis-ink);
  font-size: 0.88rem;
  margin: 0;
}}

.mis-clinical-title > span {{
  min-width: 1.65rem;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: #e8f4f2;
  color: var(--mis-action);
  font-size: 0.7rem;
  font-weight: 800;
  text-align: center;
}}

.mis-clinical-list {{
  max-height: 15rem;
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: #bfd3de transparent;
}}

.mis-clinical-item {{
  padding: 0.62rem 0.05rem;
  border-bottom: 1px solid #e8f0f4;
}}

.mis-clinical-item:last-child {{
  border-bottom: 0;
}}

.mis-clinical-item strong,
.mis-clinical-item span {{
  display: block;
}}

.mis-clinical-item strong {{
  color: var(--mis-ink);
  font-size: 0.78rem;
  font-weight: 690;
  line-height: 1.35;
}}

.mis-clinical-item span {{
  color: var(--mis-muted);
  font-size: 0.7rem;
  line-height: 1.35;
  margin-top: 0.2rem;
}}

.mis-allergy-item {{
  margin: 0.55rem 0;
  padding: 0.58rem 0.65rem;
  border: 1px solid rgba(212, 136, 23, 0.22);
  border-radius: 0.65rem;
  background: rgba(212, 136, 23, 0.07);
}}

.mis-empty-copy {{
  color: var(--mis-muted);
  font-size: 0.75rem;
  padding: 0.8rem 0;
}}

.mis-flag-card {{
  min-height: 8.3rem;
  padding: 0.05rem 0 0.15rem 0.35rem;
}}

.mis-flag-topline {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.55rem;
}}

.mis-flag-topline span {{
  color: var(--mis-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.mis-flag-topline b {{
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  font-size: 0.65rem;
}}

.mis-flag-card h3 {{
  color: var(--mis-ink);
  font-size: 1.05rem;
  line-height: 1.25;
  margin: 0 0 0.42rem;
}}

.mis-flag-card p {{
  color: var(--mis-muted);
  font-size: 0.82rem;
  line-height: 1.45;
  margin: 0;
}}

.mis-flag-critical .mis-flag-topline b {{
  color: var(--mis-critical);
  background: rgba(180, 35, 60, 0.1);
}}

.mis-flag-warning .mis-flag-topline b {{
  color: #9a5e08;
  background: rgba(212, 136, 23, 0.12);
}}

.mis-flag-info .mis-flag-topline b {{
  color: #096d9e;
  background: rgba(22, 140, 202, 0.1);
}}

.mis-no-signals {{
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(16, 168, 137, 0.2);
  border-radius: 0.9rem;
  background: rgba(16, 168, 137, 0.06);
}}

.mis-no-signals > span {{
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--mis-teal);
  color: white;
  font-weight: 800;
}}

.mis-no-signals strong {{
  color: var(--mis-ink);
  font-size: 0.85rem;
}}

.mis-no-signals p {{
  color: var(--mis-muted);
  font-size: 0.75rem;
  margin: 0.1rem 0 0;
}}

.mis-summary-empty {{
  padding: 1.2rem;
  border: 1px dashed #bfd3de;
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.55);
  color: var(--mis-muted);
  font-size: 0.85rem;
  text-align: center;
}}

.mis-latest-value {{
  min-height: 6.3rem;
  margin-bottom: 0.75rem;
  padding: 0.8rem 0.9rem;
  border: 1px solid #deeaef;
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 0.18rem 0.75rem rgba(8, 42, 76, 0.04);
}}

.mis-latest-value > span {{
  display: block;
  min-height: 2rem;
  color: var(--mis-muted);
  font-size: 0.72rem;
  line-height: 1.3;
}}

.mis-latest-value > strong {{
  display: block;
  color: var(--mis-ink);
  font-size: 1.25rem;
  line-height: 1.2;
  margin: 0.2rem 0 0.45rem;
}}

.mis-latest-meta {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}}

.mis-latest-meta small {{
  color: var(--mis-muted);
  font-size: 0.67rem;
}}

.mis-latest-badge {{
  min-height: auto !important;
  padding: 0.13rem 0.38rem;
  border-radius: 999px;
  background: rgba(16, 168, 137, 0.1);
  color: var(--mis-action) !important;
  font-size: 0.61rem !important;
  font-weight: 750;
}}

[data-testid="stSegmentedControl"] {{
  margin: 0.4rem 0 1.15rem;
}}

[data-testid="stSegmentedControl"] > div {{
  padding: 0.25rem;
  border: 1px solid var(--mis-border);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 0.18rem 0.8rem rgba(8, 42, 76, 0.04);
}}

[data-testid="stSegmentedControl"] button {{
  border-radius: 0.65rem;
  transition: background-color 180ms ease, color 180ms ease, transform 180ms ease;
}}

[data-testid="stSegmentedControl"] button:hover {{
  transform: translateY(-1px);
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  gap: 0.35rem;
  padding: 0.2rem;
  border-bottom: 0;
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
  height: 2.35rem;
  padding: 0 0.85rem;
  border-radius: 0.7rem;
  color: var(--mis-muted);
  font-size: 0.78rem;
  transition: background-color 180ms ease, color 180ms ease;
}}

[data-testid="stTabs"] [aria-selected="true"] {{
  background: #e5f2f1;
  color: var(--mis-action);
}}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
  display: none;
}}

[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: var(--mis-border);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 0.2rem 0.9rem rgba(8, 42, 76, 0.045);
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}}

[data-testid="stVerticalBlockBorderWrapper"]:hover {{
  border-color: #bfd3de;
  box-shadow: var(--mis-shadow);
}}

[data-testid="stVerticalBlockBorderWrapper"]:has(.mis-patient-marker) {{
  border-top: 0.22rem solid var(--mis-teal);
}}

[data-testid="stVerticalBlockBorderWrapper"]:has(.mis-flag-critical) {{
  border-left: 0.22rem solid var(--mis-critical);
}}

[data-testid="stVerticalBlockBorderWrapper"]:has(.mis-flag-warning) {{
  border-left: 0.22rem solid var(--mis-amber);
}}

[data-testid="stVerticalBlockBorderWrapper"]:has(.mis-flag-info) {{
  border-left: 0.22rem solid var(--mis-blue);
}}

[data-testid="stVerticalBlockBorderWrapper"]:has(.mis-summary-marker) {{
  border-top: 0.22rem solid var(--mis-blue);
}}

[data-testid="stMetric"] {{
  padding: 0.7rem 0.8rem;
  border-radius: 0.8rem;
  background: #f7fafc;
  border: 1px solid #e2edf2;
}}

[data-testid="stMetricLabel"] {{
  color: var(--mis-muted);
}}

[data-testid="stMetricValue"] {{
  color: var(--mis-ink);
  font-weight: 760;
}}

[data-testid="stPlotlyChart"] {{
  overflow: hidden;
  border: 1px solid var(--mis-border);
  border-radius: 1rem;
  background: white;
  box-shadow: var(--mis-shadow);
}}

[data-testid="stDataFrame"] {{
  overflow: hidden;
  border: 1px solid var(--mis-border);
  border-radius: 1rem;
  box-shadow: var(--mis-shadow);
}}

[data-testid="stExpander"] {{
  border-color: var(--mis-border);
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.72);
}}

.mis-enter {{
  animation: mis-fade-up 300ms cubic-bezier(0.2, 0.75, 0.25, 1) both;
}}

@keyframes mis-fade-up {{
  from {{ opacity: 0; transform: translateY(0.4rem); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

@media (max-width: 720px) {{
  [data-testid="stMainBlockContainer"] {{
    padding-left: 1rem;
    padding-right: 1rem;
  }}
  .mis-app-mark {{
    display: none;
  }}
  .mis-empty-state {{
    margin-top: 2rem;
    padding: 2rem 1.25rem;
  }}
}}

@media (prefers-reduced-motion: reduce) {{
  .mis-enter,
  [data-testid="stSegmentedControl"] button,
  [data-testid="stVerticalBlockBorderWrapper"] {{
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }}
}}
"""
