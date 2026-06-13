"""
Аналітична панель моніторингу якості освіти
Шаргород та Шаргородський район — Вінницька область
Streamlit + Plotly
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import random
from datetime import datetime
import io

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

# ─── Конфігурація сторінки ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Шаргородський ЗЗСО — Моніторинг якості освіти",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Стилі ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Основний фон */
    .stApp { background-color: #F5F7FA; color: #1A202C; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    [data-testid="stSidebar"] * { color: #1A202C !important; }

    /* Метрики */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] { color: #1A202C !important; font-size: 28px !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* Заголовки секцій */
    .section-title {
        color: #1A202C;
        font-size: 16px;
        font-weight: 700;
        margin: 24px 0 8px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #E2E8F0;
    }

    /* Таблиця */
    [data-testid="stDataFrame"] { background: #FFFFFF; border-radius: 10px; }
    .dataframe { background: #FFFFFF !important; color: #1A202C !important; }

    /* Selectbox — темніший фон у сайдбарі */
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {
        background: #DDE3ED !important;
        border: 1px solid #B8C4D4 !important;
        border-radius: 8px !important;
        color: #1A202C !important;
    }
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div:hover {
        background: #CDD5E0 !important;
        border-color: #94A3B8 !important;
    }
    /* Підписи фільтрів */
    [data-testid="stSidebar"] label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    /* Приховати зайве */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Картка школи */
    .school-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .rank-gold   { color: #D97706; font-size: 20px; }
    .rank-silver { color: #94A3B8; font-size: 20px; }
    .rank-bronze { color: #B45309; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# ─── Дані ────────────────────────────────────────────────────────────────────
SCHOOLS = [
    "Шаргородський ліцей №1",
    "Шаргородська гімназія",
    "Шаргородський ліцей №2",
    "Мурафська гімназія",
    "Джуринська філія",
    "Вербівська філія",
    "Кліщівська філія",
    "Яришівська філія",
    "Плебанівський ліцей",
    "Перепільчинецька гімназія",
    "Носиківська гімназія",
    "Буднянська гімназія",
    "Писарівська філія",
    "Політанківська філія",
    "Сапіжанська гімназія",
    "Гибалівська гімназія",
    "Голинчинецька гімназія",
    "Деребчинський ліцей",
    "Довжанський ліцей",
    "Зведенівський ліцей",
    "Івашковецька гімназія",
    "Клекотинський ліцей",
    "Козлівська гімназія",
    "Копистиринська гімназія",
    "Лозівська гімназія",
    "Михайлівський ліцей",
    "Пасинківська гімназія",
    "Пеньківський ліцей",
    "Покутинський ліцей",
    "Рахнівсько-Лісовий ліцей",
    "Рахнівсько-Лісовий ліцей №2",
    "Руданська гімназія",
    "Слободо-Шаргородський ліцей",
    "Федорівський ліцей",
    "Хоменківський ліцей",
    "Юхимівський ліцей",
]
SUBJECTS  = ["Математика", "Українська мова", "Англійська мова", "Історія", "Біологія", "Хімія", "Фізика", "Українська література", "Географія"]
YEARS     = [2021, 2022, 2023, 2024, 2025]
MONTHS_LBL = ["Вер","Жов","Лис","Гру","Січ","Лют","Бер","Кві","Тра","Чер"]
MONTHS_NUM = list(range(9, 13)) + list(range(1, 7))

COLORS = {
    "blue":   "#2D8CF0", "green":  "#18C964",
    "amber":  "#F5A524", "red":    "#F31260",
    "purple": "#9353D3", "teal":   "#06B7DB",
    "pink":   "#FF69B4", "lime":   "#7EE787",
}
PALETTE = list(COLORS.values())
BG      = "#F5F7FA"
CARD    = "#FFFFFF"
BORDER  = "#E2E8F0"
TEXT    = "#1A202C"
MUTED   = "#64748B"

def seed_val(school, year=0, key=""):
    return abs(hash(f"{school}{year}{key}")) % 10000

def nmt_score(school, year, subject):
    random.seed(seed_val(school, year, subject))
    base  = random.randint(140, 185)
    trend = (year - 2021) * random.randint(-1, 3)
    return min(200, max(100, base + trend))

def attendance(school, month):
    random.seed(seed_val(school, month))
    return round(random.uniform(88.0, 98.5), 1)

def teacher_load(school):
    random.seed(seed_val(school))
    total    = random.randint(28, 55)
    over     = random.randint(2, max(2, total // 5))
    vacant   = random.randint(0, 3)
    normal   = total - over - vacant
    return total, normal, over, vacant

def grade_dist(school):
    random.seed(seed_val(school, 999))
    exc  = random.randint(18, 32)
    good = random.randint(30, 42)
    sat  = random.randint(18, 28)
    poor = max(0, 100 - exc - good - sat)
    return exc, good, sat, poor

def dropout(school):
    random.seed(seed_val(school, 77))
    return random.randint(0, 8)

def composite_index(school, year):
    avg_nmt = sum(nmt_score(school, year, s) for s in SUBJECTS) / len(SUBJECTS)
    avg_att = sum(attendance(school, m) for m in MONTHS_NUM) / len(MONTHS_NUM)
    exc, *_ = grade_dist(school)
    drops   = dropout(school)
    return round(
        (avg_nmt - 100) / 100 * 40 +
        (avg_att - 85)  / 15  * 30 +
        exc / 30 * 20 +
        max(0, 10 - drops),
        1
    )

# ─── Plotly layout helper ─────────────────────────────────────────────────────
def dark_layout(**kw):
    return dict(
        paper_bgcolor=CARD,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Segoe UI, Arial"),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            bgcolor=CARD, bordercolor=BORDER, borderwidth=1,
            font=dict(color=MUTED, size=11)
        ),
        **kw
    )

def axis_style(**kw):
    return dict(
        gridcolor=BORDER, zerolinecolor=BORDER,
        tickfont=dict(color=MUTED, size=11),
        **kw
    )

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏫 Шаргород")
    st.markdown("<small style='color:#64748B'>Шаргородський район — моніторинг якості освіти</small>",
                unsafe_allow_html=True)
    st.divider()

    page = st.selectbox(
        "Розділ",
        ["📊 Огляд", "📝 НМТ та успішність",
         "📅 Відвідуваність", "👩‍🏫 Кадри", "🏫 Порівняння шкіл",
         "🗺️ Громада", "📰 Новини та події"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("**Фільтри**")
    sel_school  = st.selectbox("🏫 Школа",    SCHOOLS)
    sel_year    = st.selectbox("📅 Рік",       YEARS, index=len(YEARS)-1)
    sel_subject = st.selectbox("📚 Предмет",   SUBJECTS)

    # ─── Блок експорту/імпорту ───────────────────────────────────────────────
    st.divider()
    st.markdown("**📂 Дані**")

    if st.button("📥 Експорт у CSV"):
        export_df = pd.DataFrame({
            "Школа": SCHOOLS,
            "Бал_НМТ": [nmt_score(s, sel_year, "Математика") for s in SCHOOLS],
            "Відвідуваність": [attendance(s, 1) for s in SCHOOLS]
        })
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("Завантажити CSV", csv, "shargorod_data.csv", "text/csv")

    uploaded_file = st.file_uploader("📤 Імпорт даних (CSV/Excel)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_imported = pd.read_csv(uploaded_file)
            else:
                df_imported = pd.read_excel(uploaded_file)
            st.success("Файл успішно завантажено!")
            st.write("Попередній перегляд:", df_imported.head())
        except Exception as e:
            st.error(f"Помилка при читанні файлу: {e}")

    st.divider()
    st.caption(f"Оновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

# ─── Page helpers ─────────────────────────────────────────────────────────────
def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 1 — ОГЛЯД
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Огляд":
    st.title("📊 Загальний огляд — Шаргородський район")

    avg_nmt   = int(sum(nmt_score(sel_school, sel_year, s) for s in SUBJECTS) / len(SUBJECTS))
    avg_prev  = int(sum(nmt_score(sel_school, sel_year - 1, s) for s in SUBJECTS) / len(SUBJECTS))
    avg_att   = round(sum(attendance(sel_school, m) for m in MONTHS_NUM) / len(MONTHS_NUM), 1)
    total_t, norm_t, over_t, vac_t = teacher_load(sel_school)
    exc, good, sat, poor = grade_dist(sel_school)
    drops = dropout(sel_school)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📝 Середній бал НМТ", avg_nmt, f"{avg_nmt - avg_prev:+d} vs минулий рік")
    c2.metric("📅 Відвідуваність",    f"{avg_att}%",
              "▲ норма" if avg_att >= 95 else "▼ нижче норми")
    c3.metric("👩‍🏫 Вчителів",         f"{135} осіб",
              f"⚠️ {over_t} перевант." if over_t else "✅ норма")
    c4.metric("🏆 Відмінники",        f"{exc}%", None)
    c5.metric("⚠️ Відрахованих",      f"{drops} учн.",
              "🔴 критично" if drops >= 5 else "✅ норма")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        section("НМТ по предметах")
        scores = [nmt_score(sel_school, sel_year, s) for s in SUBJECTS]
        bar_colors = [COLORS["green"] if v == max(scores) else COLORS["blue"] for v in scores]
        fig = go.Figure(go.Bar(
            x=SUBJECTS, y=scores,
            marker_color=bar_colors,
            text=scores, textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig.update_layout(
            title=f"Середній бал НМТ — {sel_year}",
            yaxis_range=[100, 205],
            **dark_layout()
        )
        fig.update_xaxes(**axis_style())
        fig.update_yaxes(**axis_style())
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        section("Відвідуваність по місяцях")
        att_vals = [attendance(sel_school, m) for m in MONTHS_NUM]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=MONTHS_LBL, y=att_vals,
            mode="lines+markers",
            line=dict(color=COLORS["green"], width=2.5),
            marker=dict(size=7, color=COLORS["green"]),
            fill="tozeroy",
            fillcolor="rgba(24,201,100,0.08)",
            name="Відвідуваність",
        ))
        fig2.add_hline(y=95, line_dash="dot",
                       line_color=COLORS["amber"],
                       annotation_text="Норма 95%",
                       annotation_font_color=COLORS["amber"])
        fig2.update_layout(
            title="Відвідуваність (%)", yaxis_range=[82, 102],
            **dark_layout()
        )
        fig2.update_xaxes(**axis_style())
        fig2.update_yaxes(**axis_style())
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        section("Розподіл успішності")
        fig3 = go.Figure(go.Pie(
            labels=["Відмінно", "Добре", "Задовільно", "Незадовільно"],
            values=[exc, good, sat, poor],
            hole=0.55,
            marker_colors=[COLORS["green"], COLORS["blue"],
                           COLORS["amber"], COLORS["red"]],
            textfont=dict(color=TEXT),
        ))
        fig3.update_layout(title="Успішність учнів", **dark_layout())
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        section("Навантаження вчителів")
        fig4 = go.Figure(go.Bar(
            x=["Норма", "Перевантаж.", "Вакансії"],
            y=[norm_t, over_t, vac_t],
            marker_color=[COLORS["green"], COLORS["amber"], COLORS["red"]],
            text=[f"{v} осіб" for v in [norm_t, over_t, vac_t]],
            textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig4.update_layout(title="Кадри школи", **dark_layout())
        fig4.update_xaxes(**axis_style())
        fig4.update_yaxes(**axis_style())
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 2 — НМТ
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📝 НМТ та успішність":
    st.title("📝 НМТ та успішність — Шаргородський район")

    section(f"Динаміка НМТ по предметах — {sel_school} (2021–2025)")
    fig = go.Figure()
    for i, subj in enumerate(SUBJECTS):
        vals = [nmt_score(sel_school, y, subj) for y in YEARS]
        fig.add_trace(go.Scatter(
            x=[str(y) for y in YEARS], y=vals,
            mode="lines+markers",
            name=subj,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
            marker=dict(size=7),
        ))
    fig.update_layout(title="Бали НМТ по роках", **dark_layout())
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style(range=[95, 205]))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        section(f"Порівняння шкіл — {sel_subject}, {sel_year}")
        scores = [nmt_score(s, sel_year, sel_subject) for s in SCHOOLS]
        short  = [s.split()[1][:8] if len(s.split()) > 1 else s[:8] for s in SCHOOLS]
        fig2 = go.Figure(go.Bar(
            x=short, y=scores,
            marker_color=[COLORS["green"] if v == max(scores) else
                          COLORS["red"] if v == min(scores) else
                          COLORS["blue"] for v in scores],
            text=scores, textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig2.update_layout(title=f"{sel_subject}", yaxis_range=[95, 205], **dark_layout())
        fig2.update_xaxes(**axis_style())
        fig2.update_yaxes(**axis_style())
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        section(f"Теплова карта НМТ — {sel_year}")
        matrix = [[nmt_score(s, sel_year, subj) for subj in SUBJECTS] for s in SCHOOLS]
        short_s = [s.split()[1][:10] if len(s.split()) > 1 else s[:10] for s in SCHOOLS]
        fig3 = go.Figure(go.Heatmap(
            z=matrix, x=SUBJECTS, y=short_s,
            colorscale=[[0, COLORS["red"]],
                        [0.5, COLORS["amber"]],
                        [1, COLORS["green"]]],
            text=[[str(v) for v in row] for row in matrix],
            texttemplate="%{text}",
            textfont=dict(size=11, color="white"),
            zmin=100, zmax=200,
        ))
        fig3.update_layout(title="Бали по всіх школах і предметах", **dark_layout())
        st.plotly_chart(fig3, use_container_width=True)

    section("Рейтинг шкіл по обраному предмету")
    scores2 = [(s, nmt_score(s, sel_year, sel_subject)) for s in SCHOOLS]
    scores2.sort(key=lambda x: x[1], reverse=True)

    top_cols = st.columns(3)
    medals = [("🥇", "#FFD700", "#FFF9E6"), ("🥈", "#A8A9AD", "#F5F5F5"), ("🥉", "#CD7F32", "#FDF3E7")]
    for i in range(3):
        sc, sc_val = scores2[i]
        medal, color, bg = medals[i]
        with top_cols[i]:
            st.markdown(f"""
<div style='background:{bg};border:2px solid {color};border-radius:14px;
     padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.10)'>
  <div style='font-size:36px'>{medal}</div>
  <div style='font-size:13px;color:#374151;font-weight:600;margin:8px 0 4px'>{sc}</div>
  <div style='font-size:32px;font-weight:800;color:{color}'>{sc_val}</div>
  <div style='font-size:11px;color:#64748B'>балів НМТ</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig_rank = go.Figure(go.Bar(
        y=[f"#{i+1}  {sc[:25]}" for i, (sc, _) in enumerate(scores2)],
        x=[v for _, v in scores2],
        orientation="h",
        marker_color=[
            COLORS["green"] if v == scores2[0][1] else
            COLORS["blue"]  if v >= 160 else
            COLORS["amber"] if v >= 145 else
            COLORS["red"]   for _, v in scores2
        ],
        text=[str(v) for _, v in scores2],
        textposition="outside",
        textfont=dict(color=TEXT, size=12),
    ))
    fig_rank.update_layout(
        title=f"Повний рейтинг — {sel_subject} {sel_year}",
        xaxis_range=[95, 205],
        height=900,
        **dark_layout()
    )
    fig_rank.update_xaxes(**axis_style())
    fig_rank.update_yaxes(**axis_style())
    st.plotly_chart(fig_rank, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 3 — ВІДВІДУВАНІСТЬ
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Відвідуваність":
    st.title("📅 Відвідуваність — Шаргородський район")

    section("Помісячна відвідуваність по всіх школах")
    fig = go.Figure()
    for i, sc in enumerate(SCHOOLS):
        vals = [attendance(sc, m) for m in MONTHS_NUM]
        fig.add_trace(go.Scatter(
            x=MONTHS_LBL, y=vals,
            mode="lines+markers",
            name=sc[:18],
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            marker=dict(size=6),
        ))
    fig.add_hline(y=95, line_dash="dot", line_color=COLORS["amber"],
                  annotation_text="Норма 95%",
                  annotation_font_color=COLORS["amber"])
    fig.update_layout(title="Відвідуваність (%) по місяцях",
                      yaxis_range=[84, 101], **dark_layout())
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style())
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        section(f"Деталі — {sel_school}")
        att_vals = [attendance(sel_school, m) for m in MONTHS_NUM]
        bar_colors = [COLORS["green"] if v >= 95 else
                      COLORS["amber"] if v >= 90 else COLORS["red"]
                      for v in att_vals]
        fig2 = go.Figure(go.Bar(
            x=MONTHS_LBL, y=att_vals,
            marker_color=bar_colors,
            text=[f"{v}%" for v in att_vals],
            textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig2.add_hline(y=95, line_dash="dot", line_color=COLORS["amber"])
        fig2.update_layout(title=sel_school[:30],
                            yaxis_range=[82, 102], **dark_layout())
        fig2.update_xaxes(**axis_style())
        fig2.update_yaxes(**axis_style())
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        section("Середня відвідуваність по школах")
        avgs = [(sc, round(sum(attendance(sc, m) for m in MONTHS_NUM) / len(MONTHS_NUM), 1))
                for sc in SCHOOLS]
        avgs.sort(key=lambda x: x[1], reverse=True)
        df = pd.DataFrame(avgs, columns=["Школа", "Відвідуваність %"])
        fig3 = go.Figure(go.Bar(
            y=[a[0][:20] for a in avgs],
            x=[a[1] for a in avgs],
            orientation="h",
            marker_color=[COLORS["green"] if v >= 95 else
                          COLORS["amber"] if v >= 92 else COLORS["red"]
                          for _, v in avgs],
            text=[f"{v}%" for _, v in avgs],
            textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig3.update_layout(title="Рейтинг шкіл",
                            xaxis_range=[82, 102], **dark_layout())
        fig3.update_xaxes(**axis_style())
        fig3.update_yaxes(**axis_style())
        st.plotly_chart(fig3, use_container_width=True)

    section("Зведена таблиця відвідуваності")
    table_data = {
        "Школа": SCHOOLS,
        **{lbl: [attendance(sc, m) for sc in SCHOOLS]
           for lbl, m in zip(MONTHS_LBL, MONTHS_NUM)},
        "Середня": [round(sum(attendance(sc, m) for m in MONTHS_NUM) / len(MONTHS_NUM), 1)
                    for sc in SCHOOLS]
    }
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 4 — КАДРИ
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👩‍🏫 Кадри":
    st.title("👩‍🏫 Кадрова статистика — Шаргородський район")

    loads = {sc: teacher_load(sc) for sc in SCHOOLS}
    total_all = sum(v[0] for v in loads.values())
    over_all  = sum(v[2] for v in loads.values())
    vac_all   = sum(v[3] for v in loads.values())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👩‍🏫 Вчителів всього",  f"{total_all} осіб")
    c2.metric("✅ Норм. навантаж.",     f"{total_all - over_all - vac_all} осіб")
    c3.metric("⚠️ Перевантажені",       f"{over_all} осіб",
              f"{round(over_all/total_all*100)}% від загалу")
    c4.metric("🔴 Вакантних посад",     f"{vac_all} місць")

    section("Розподіл навантаження по школах")
    fig = go.Figure()
    short = [s.split()[1][:10] if len(s.split()) > 1 else s[:8] for s in SCHOOLS]
    for label, idx, color in [("Норма", 1, COLORS["green"]),
                               ("Перевантаж.", 2, COLORS["amber"]),
                               ("Вакансії", 3, COLORS["red"])]:
        fig.add_trace(go.Bar(
            name=label,
            x=short,
            y=[loads[sc][idx] for sc in SCHOOLS],
            marker_color=color,
            text=[loads[sc][idx] for sc in SCHOOLS],
            textposition="inside",
            textfont=dict(color="white"),
        ))
    fig.update_layout(barmode="stack",
                      title="Структура кадрів (осіб)",
                      **dark_layout())
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style())
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        section("Частка перевантажених вчителів (%)")
        pcts  = [round(loads[sc][2] / loads[sc][0] * 100) for sc in SCHOOLS]
        fig2  = go.Figure(go.Bar(
            x=short, y=pcts,
            marker_color=[COLORS["red"] if p >= 20 else COLORS["amber"] if p >= 10
                          else COLORS["green"] for p in pcts],
            text=[f"{p}%" for p in pcts],
            textposition="outside",
            textfont=dict(color=TEXT),
        ))
        fig2.update_layout(title="% перевантажених", **dark_layout())
        fig2.update_xaxes(**axis_style())
        fig2.update_yaxes(**axis_style(range=[0, max(pcts) + 10]))
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        section("Розподіл успішності учнів")
        exc_vals  = [grade_dist(sc)[0] for sc in SCHOOLS]
        good_vals = [grade_dist(sc)[1] for sc in SCHOOLS]
        sat_vals  = [grade_dist(sc)[2] for sc in SCHOOLS]
        poor_vals = [grade_dist(sc)[3] for sc in SCHOOLS]
        fig3 = go.Figure()
        for label, vals, col in [
            ("Відмінно",      exc_vals,  COLORS["green"]),
            ("Добре",         good_vals, COLORS["blue"]),
            ("Задовільно",    sat_vals,  COLORS["amber"]),
            ("Незадовільно",  poor_vals, COLORS["red"]),
        ]:
            fig3.add_trace(go.Bar(name=label, x=short, y=vals,
                                   marker_color=col))
        fig3.update_layout(barmode="stack", title="Успішність (%)", **dark_layout())
        fig3.update_xaxes(**axis_style())
        fig3.update_yaxes(**axis_style())
        st.plotly_chart(fig3, use_container_width=True)

    section("Зведена таблиця кадрів")
    df = pd.DataFrame({
        "Школа":           SCHOOLS,
        "Всього":          [loads[s][0] for s in SCHOOLS],
        "Норма":           [loads[s][1] for s in SCHOOLS],
        "Перевантаж.":     [loads[s][2] for s in SCHOOLS],
        "Вакансії":        [loads[s][3] for s in SCHOOLS],
        "% перевантаж.":   [f"{round(loads[s][2]/loads[s][0]*100)}%" for s in SCHOOLS],
        "Відрахованих":    [dropout(s) for s in SCHOOLS],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 5 — ПОРІВНЯННЯ ШКІЛ
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏫 Порівняння шкіл":
    st.title("🏫 Порівняння закладів — Шаргородський район")

    section(f"Інтегральний індекс якості освіти — {sel_year}")
    composites = [(sc, composite_index(sc, sel_year)) for sc in SCHOOLS]
    composites.sort(key=lambda x: x[1], reverse=True)
    names  = [c[0] for c in composites]
    values = [c[1] for c in composites]

    fig = go.Figure(go.Bar(
        y=[n[:22] for n in names], x=values,
        orientation="h",
        marker_color=[
            COLORS["green"]  if v >= 70 else
            COLORS["amber"]  if v >= 55 else
            COLORS["red"] for v in values
        ],
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        textfont=dict(color=TEXT, size=12),
    ))
    fig.update_layout(title="Індекс (0–100)",
                      xaxis_range=[0, 100], **dark_layout())
    fig.update_xaxes(**axis_style())
    fig.update_yaxes(**axis_style())
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)

    with col_l:
        section(f"Scatter: НМТ vs Відвідуваність ({sel_year})")
        avg_nmts = [sum(nmt_score(sc, sel_year, s) for s in SUBJECTS) / len(SUBJECTS)
                    for sc in SCHOOLS]
        avg_atts = [sum(attendance(sc, m) for m in MONTHS_NUM) / len(MONTHS_NUM)
                    for sc in SCHOOLS]
        idxs     = [composite_index(sc, sel_year) for sc in SCHOOLS]
        fig2 = go.Figure(go.Scatter(
            x=avg_nmts, y=avg_atts,
            mode="markers+text",
            text=[s.split()[1][:6] if len(s.split()) > 1 else s[:6] for s in SCHOOLS],
            textposition="top center",
            textfont=dict(color=TEXT, size=10),
            marker=dict(
                size=[i / 2 + 12 for i in idxs],
                color=idxs,
                colorscale=[[0, COLORS["red"]], [0.5, COLORS["amber"]], [1, COLORS["green"]]],
                showscale=True,
                colorbar=dict(title="Індекс", tickfont=dict(color=MUTED)),
            ),
        ))
        fig2.update_layout(
            title="Бульбашкова діаграма (розмір = індекс)",
            xaxis_title="Середній НМТ", yaxis_title="Відвідуваність %",
            **dark_layout()
        )
        fig2.update_xaxes(**axis_style())
        fig2.update_yaxes(**axis_style())
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        section("Radar: профіль обраної школи")
        categories = ["НМТ", "Відвідуваність", "Відмінники", "Кадри", "Без відрахувань"]
        avg_nmt_v = sum(nmt_score(sel_school, sel_year, s) for s in SUBJECTS) / len(SUBJECTS)
        avg_att_v = sum(attendance(sel_school, m) for m in MONTHS_NUM) / len(MONTHS_NUM)
        exc_v, *_ = grade_dist(sel_school)
        total_v, norm_v, *_ = teacher_load(sel_school)
        drop_v = dropout(sel_school)
        vals_radar = [
            round((avg_nmt_v - 100) / 100 * 100, 1),
            round((avg_att_v - 85) / 15 * 100, 1),
            round(exc_v / 30 * 100, 1),
            round(norm_v / total_v * 100, 1),
            round(max(0, 10 - drop_v) / 10 * 100, 1),
        ]
        fig3 = go.Figure(go.Scatterpolar(
            r=vals_radar + [vals_radar[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(45,140,240,0.2)",
            line=dict(color=COLORS["blue"], width=2),
            marker=dict(size=7, color=COLORS["blue"]),
        ))
        fig3.update_layout(
            polar=dict(
                bgcolor=BG,
                radialaxis=dict(visible=True, range=[0, 100],
                                gridcolor=BORDER,
                                tickfont=dict(color=MUTED, size=9)),
                angularaxis=dict(gridcolor=BORDER,
                                 tickfont=dict(color=TEXT, size=11)),
            ),
            title=f"Профіль: {sel_school[:22]}",
            **dark_layout()
        )
        st.plotly_chart(fig3, use_container_width=True)

    section("Зведена таблиця всіх показників")
    table_rows = []
    for sc in SCHOOLS:
        avg_nmt = round(sum(nmt_score(sc, sel_year, s) for s in SUBJECTS) / len(SUBJECTS), 1)
        avg_att = round(sum(attendance(sc, m) for m in MONTHS_NUM) / len(MONTHS_NUM), 1)
        total, _, over, vac = teacher_load(sc)
        exc, *_ = grade_dist(sc)
        drops = dropout(sc)
        idx = composite_index(sc, sel_year)
        table_rows.append({
            "Школа": sc, "НМТ сер.": avg_nmt,
            "Відвід. %": avg_att, "Вчителів": total,
            "Перевантаж.": over, "Вакансії": vac,
            "Відмінники %": exc, "Відрах.": drops,
            "Індекс": idx,
        })
    df = pd.DataFrame(table_rows).sort_values("Індекс", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 6 — ГРОМАДА
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Громада":
    st.title("🗺️ Шаргородська міська громада")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏙️ Місто", "1", "Шаргород")
    col2.metric("🏘️ Селища", "4", "Лісничівка, Лукашівка, Мишівське, Оліхи")
    col3.metric("🏡 Сел", "27", "населених пунктів")
    col4.metric("📋 Старостинських округів", "9", "")

    st.divider()

    col_l, col_r = st.columns([1, 1])

    with col_l:
        section("🏙️ Місто")
        st.markdown("""
<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:14px 18px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06)'>
  <span style='font-size:20px'>🏙️</span>&nbsp;&nbsp;<strong style='color:#1A202C;font-size:15px'>Шаргород</strong>
  <span style='float:right;background:#2D8CF0;color:white;border-radius:6px;padding:2px 10px;font-size:12px'>адмін. центр</span>
</div>
""", unsafe_allow_html=True)

        section("🏘️ Селища")
        selyscha = ["Лісничівка", "Лукашівка", "Мишівське", "Оліхи"]
        for s in selyscha:
            st.markdown(f"""
<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:8px;padding:10px 16px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
  <span style='font-size:16px'>🏘️</span>&nbsp;&nbsp;<span style='color:#1A202C;font-size:14px'>{s}</span>
</div>""", unsafe_allow_html=True)

        section("🏡 Села (27)")
        villages = [
            "Андріївка", "Борівське", "Будне", "Гибалівка", "Грелівка",
            "Дерев'янки", "Дубинки", "Івашківці", "Калинівка", "Козлівка",
            "Конатківці", "Копистирин", "Кропивня", "Лозова", "Мальовниче",
            "Носиківка", "Пасинки", "Перепільчинці", "Писарівка", "Плебанівка",
            "Політанки", "Поляна", "Роля", "Руданське", "Слобода-Шаргородська",
            "Сурогатка", "Теклівка",
        ]
        v_cols = st.columns(3)
        for i, v in enumerate(villages):
            with v_cols[i % 3]:
                st.markdown(f"""
<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:7px;padding:7px 12px;margin-bottom:5px;font-size:13px;color:#374151'>
  🏡 {v}
</div>""", unsafe_allow_html=True)

    with col_r:
        section("📋 Старостинські округи")
        starosty = [
            ("Івашковецький",      "Івашківці, Калинівка, Дубинки"),
            ("Козлівський",        "Козлівка, Борівське, Будне"),
            ("Копистиринський",    "Копистирин, Конатківці, Гибалівка"),
            ("Лозівський",         "Лозова, Грелівка, Дерев'янки"),
            ("Носиківський",       "Носиківка, Андріївка, Пасинки"),
            ("Перепільчинецький",  "Перепільчинці, Писарівка, Поляна"),
            ("Плебанівський",      "Плебанівка, Мальовниче, Роля"),
            ("Політанківський",    "Політанки, Кропивня, Теклівка"),
            ("Руданський",         "Руданське, Слобода-Шаргородська, Сурогатка"),
        ]
        colors_s = [
            "#2D8CF0","#18C964","#F5A524","#9353D3","#F31260",
            "#06B7DB","#FF69B4","#7EE787","#FB923C",
        ]
        for i, (name, villages_in) in enumerate(starosty):
            col = colors_s[i % len(colors_s)]
            st.markdown(f"""
<div style='background:#FFFFFF;border-left:4px solid {col};border-radius:0 10px 10px 0;
     border-top:1px solid #E2E8F0;border-right:1px solid #E2E8F0;border-bottom:1px solid #E2E8F0;
     padding:10px 16px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
  <strong style='color:#1A202C;font-size:14px'>{name} округ</strong><br>
  <span style='color:#64748B;font-size:12px'>📍 {villages_in}</span>
</div>""", unsafe_allow_html=True)

        st.divider()

        section("📊 Структура населених пунктів")
        fig = go.Figure(go.Pie(
            labels=["Місто", "Селища", "Села"],
            values=[1, 4, 27],
            hole=0.5,
            marker_colors=[COLORS["blue"], COLORS["amber"], COLORS["green"]],
            textfont=dict(color=TEXT, size=13),
            textinfo="label+value",
        ))
        fig.update_layout(
            title="Всього 32 населених пункти",
            **dark_layout(),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# СТОРІНКА 7 — НОВИНИ ТА ПОДІЇ
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📰 Новини та події":
    st.title("📰 Новини та події — Шаргородська громада")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📰 Новин цього місяця", "12", "+3 vs минулий")
    col2.metric("🎉 Заходів заплановано", "8", "на червень")
    col3.metric("🏆 Досягнень учнів", "24", "+5 цього року")
    col4.metric("📢 Оголошень", "5", "активних")

    st.divider()

    col_l, col_r = st.columns([3, 2])

    with col_l:
        section("📌 Останні новини")

        news = [
            {
                "date": "10.06.2025",
                "tag": "🏆 Досягнення",
                "tag_color": "#18C964",
                "title": "Учні Шаргородського ліцею №1 перемогли на обласній олімпіаді з математики",
                "text": "Троє учнів здобули призові місця на обласному етапі Всеукраїнської олімпіади. Вітаємо переможців та їхніх вчителів!",
                "school": "Шаргородський ліцей №1",
            },
            {
                "date": "07.06.2025",
                "tag": "📋 Адмінінформація",
                "tag_color": "#2D8CF0",
                "title": "Затверджено план роботи шкіл на 2025/2026 навчальний рік",
                "text": "Відділ освіти затвердив календарний план заходів для всіх закладів громади на наступний навчальний рік.",
                "school": "Відділ освіти",
            },
            {
                "date": "03.06.2025",
                "tag": "🎉 Захід",
                "tag_color": "#9353D3",
                "title": "День захисту дітей: святковий концерт у Шаргородській гімназії",
                "text": "1 червня у гімназії відбувся великий святковий концерт за участі учнів усіх класів. Захід зібрав понад 300 глядачів.",
                "school": "Шаргородська гімназія",
            },
            {
                "date": "28.05.2025",
                "tag": "🔧 Інфраструктура",
                "tag_color": "#F5A524",
                "title": "Завершено ремонт спортзалу у Мурафській гімназії",
                "text": "Після капітального ремонту відкрито оновлений спортивний зал. Роботи фінансувались з районного бюджету.",
                "school": "Мурафська гімназія",
            },
            {
                "date": "22.05.2025",
                "tag": "📚 Освіта",
                "tag_color": "#06B7DB",
                "title": "Старт пілотного проєкту цифрової освіти у трьох школах району",
                "text": "Шаргородський ліцей №2, Плебанівський ліцей та Деребчинський ліцей розпочали пілот з впровадження цифрових інструментів навчання.",
                "school": "Три заклади",
            },
            {
                "date": "15.05.2025",
                "tag": "🏆 Досягнення",
                "tag_color": "#18C964",
                "title": "Команда Носиківської гімназії — чемпіон районної спартакіади",
                "text": "За підсумками весняної спартакіади серед шкіл громади перше місце посіла команда Носиківської гімназії.",
                "school": "Носиківська гімназія",
            },
        ]

        for item in news:
            st.markdown(f"""
<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
     padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06)'>
  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
    <span style='background:{item["tag_color"]}22;color:{item["tag_color"]};
          border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600'>
      {item["tag"]}
    </span>
    <span style='color:#94A3B8;font-size:12px'>📅 {item["date"]}</span>
  </div>
  <div style='font-size:15px;font-weight:700;color:#1A202C;margin-bottom:6px'>
    {item["title"]}
  </div>
  <div style='font-size:13px;color:#64748B;margin-bottom:8px'>
    {item["text"]}
  </div>
  <div style='font-size:12px;color:#94A3B8'>
    🏫 {item["school"]}
  </div>
</div>""", unsafe_allow_html=True)

    with col_r:
        section("🗓️ Заплановані заходи")

        events = [
            ("13.06.2025", "Випускний вечір — ліцей №1",        "#9353D3"),
            ("14.06.2025", "Випускний вечір — гімназія",         "#9353D3"),
            ("16.06.2025", "Педрада: підсумки року",             "#2D8CF0"),
            ("20.06.2025", "Останній дзвоник — філії",           "#18C964"),
            ("25.06.2025", "Нарада директорів шкіл",             "#F5A524"),
            ("01.09.2025", "День знань — початок нового року",   "#F31260"),
            ("10.09.2025", "Районна олімпіада з математики",     "#06B7DB"),
            ("15.10.2025", "Батьківські збори у всіх школах",    "#FF69B4"),
        ]

        for date, title, color in events:
            st.markdown(f"""
<div style='background:#FFFFFF;border-left:4px solid {color};
     border-radius:0 10px 10px 0;
     border-top:1px solid #E2E8F0;border-right:1px solid #E2E8F0;
     border-bottom:1px solid #E2E8F0;
     padding:10px 14px;margin-bottom:8px;
     box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
  <div style='font-size:11px;color:#94A3B8;margin-bottom:3px'>📅 {date}</div>
  <div style='font-size:13px;font-weight:600;color:#1A202C'>{title}</div>
</div>""", unsafe_allow_html=True)

        st.divider()
        section("📊 Новини за категоріями")

        fig_pie = go.Figure(go.Pie(
            labels=["Досягнення", "Заходи", "Адмінінфо", "Інфраструктура", "Освіта"],
            values=[8, 6, 5, 4, 3],
            hole=0.5,
            marker_colors=[
                COLORS["green"], COLORS["purple"],
                COLORS["blue"],  COLORS["amber"], COLORS["teal"]
            ],
            textfont=dict(color=TEXT, size=12),
            textinfo="label+percent",
        ))
        fig_pie.update_layout(
            title="Розподіл новин",
            height=280,
            **dark_layout()
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    section("📣 Оголошення")

    announcements = [
        ("🔴", "Прийом документів до 1 класу триває до 30 червня 2025 року.", "#F31260"),
        ("🟡", "Технічні роботи на сайті відділу освіти — 14–15 червня.", "#F5A524"),
        ("🟢", "Відкрито реєстрацію на літній мовний табір при ліцеї №1.", "#18C964"),
        ("🔵", "Опитування батьків щодо якості освіти — посилання на сайті громади.", "#2D8CF0"),
        ("🟣", "Збір заявок на участь у програмі обміну вчителями — до 1 липня.", "#9353D3"),
    ]

    ann_cols = st.columns(len(announcements))
    for col, (icon, text, color) in zip(ann_cols, announcements):
        with col:
            st.markdown(f"""
<div style='background:#FFFFFF;border-top:4px solid {color};
     border-radius:0 0 12px 12px;
     border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0;
     border-bottom:1px solid #E2E8F0;
     padding:14px 12px;text-align:center;
     box-shadow:0 1px 4px rgba(0,0,0,0.06);height:100%'>
  <div style='font-size:24px;margin-bottom:8px'>{icon}</div>
  <div style='font-size:12px;color:#374151;line-height:1.5'>{text}</div>
</div>""", unsafe_allow_html=True)
