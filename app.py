#!/usr/bin/env python3
"""
Аналітична панель моніторингу якості освіти РАЙОНО
Educational Quality Monitoring Dashboard
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
from datetime import datetime, timedelta
import json

# ── Palette ────────────────────────────────────────────────────────────────────
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_SIDEBAR   = "#0D1117"
ACCENT_BLUE  = "#2D8CF0"
ACCENT_GREEN = "#18C964"
ACCENT_AMBER = "#F5A524"
ACCENT_RED   = "#F31260"
ACCENT_PURP  = "#9353D3"
TEXT_PRIMARY = "#E6EDF3"
TEXT_MUTED   = "#8B949E"
BORDER       = "#21262D"
HOVER        = "#1F2937"

FONT_HEADER  = ("Segoe UI", 22, "bold")
FONT_TITLE   = ("Segoe UI", 13, "bold")
FONT_LABEL   = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_KPINUM  = ("Segoe UI", 28, "bold")
FONT_NAV     = ("Segoe UI", 11)

# ── Mock data generation ────────────────────────────────────────────────────────

SCHOOLS = [
    "ЗШ №1 ім. Шевченка", "ЗШ №3 «Перлина»", "ЗШ №5 ім. Франка",
    "ЗШ №7 «Ліцей»", "ЗШ №9 «Гімназія»", "ЗШ №11 «Еліт»",
    "ЗШ №13 ім. Лесі", "ЗШ №15 «Злагода»",
]

SUBJECTS_NMT = ["Математика", "Українська мова", "Англійська мова", "Історія", "Біологія"]
YEARS = [2021, 2022, 2023, 2024, 2025]


def gen_seed(school, year=0, subject=""):
    return abs(hash(school + str(year) + subject)) % 10000


def nmt_score(school, year, subject):
    random.seed(gen_seed(school, year, subject))
    base = random.randint(140, 185)
    trend = (year - 2021) * random.randint(-1, 3)
    return min(200, max(100, base + trend))


def attendance_rate(school, month):
    random.seed(gen_seed(school, month))
    return round(random.uniform(88.0, 98.5), 1)


def teacher_load(school):
    random.seed(gen_seed(school))
    total = random.randint(28, 55)
    overloaded = random.randint(2, max(2, total // 5))
    vacant = random.randint(0, 3)
    normal = total - overloaded - vacant
    return total, normal, overloaded, vacant


def grade_distribution(school):
    random.seed(gen_seed(school, 999))
    excellent = random.randint(18, 32)
    good = random.randint(30, 42)
    satisf = random.randint(18, 28)
    poor = 100 - excellent - good - satisf
    return excellent, good, satisf, max(0, poor)


def dropout_count(school):
    random.seed(gen_seed(school, 77))
    return random.randint(0, 8)


# ── Custom Canvas widgets ───────────────────────────────────────────────────────

class RoundedCard(tk.Canvas):
    def __init__(self, parent, w, h, color=BG_CARD, radius=12, **kw):
        super().__init__(parent, width=w, height=h,
                         bg=parent["bg"], highlightthickness=0, **kw)
        self._color = color
        self._radius = radius
        self._draw_bg(w, h)

    def _draw_bg(self, w, h):
        r = self._radius
        c = self._color
        self.create_polygon(
            r, 0, w - r, 0,
            w, r, w, h - r,
            w - r, h, r, h,
            0, h - r, 0, r,
            fill=c, outline=BORDER, smooth=True
        )


def draw_bar_chart(canvas, data, labels, title, x0, y0, w, h,
                   bar_color=ACCENT_BLUE, value_fmt="{:.0f}"):
    canvas.create_text(x0 + w // 2, y0 + 14, text=title,
                       fill=TEXT_PRIMARY, font=FONT_TITLE, anchor="center")
    chart_y0 = y0 + 30
    chart_h  = h - 55
    chart_w  = w - 40
    chart_x0 = x0 + 20
    max_v = max(data) if data else 1
    n = len(data)
    bar_w = max(6, (chart_w - (n + 1) * 4) // n)
    for i, (val, lbl) in enumerate(zip(data, labels)):
        bx = chart_x0 + i * (bar_w + 4) + 4
        bh = int((val / max_v) * chart_h)
        by = chart_y0 + chart_h - bh
        canvas.create_rectangle(bx, by, bx + bar_w, chart_y0 + chart_h,
                                 fill=bar_color, outline="", width=0)
        canvas.create_text(bx + bar_w // 2, by - 6,
                            text=value_fmt.format(val),
                            fill=TEXT_PRIMARY, font=FONT_SMALL, anchor="s")
        canvas.create_text(bx + bar_w // 2, chart_y0 + chart_h + 8,
                            text=lbl, fill=TEXT_MUTED, font=FONT_SMALL,
                            angle=0, anchor="n")
    canvas.create_line(chart_x0, chart_y0 + chart_h,
                       chart_x0 + chart_w, chart_y0 + chart_h,
                       fill=BORDER, width=1)


def draw_line_chart(canvas, series, labels, x0, y0, w, h, title=""):
    if title:
        canvas.create_text(x0 + w // 2, y0 + 14,
                            text=title, fill=TEXT_PRIMARY,
                            font=FONT_TITLE, anchor="center")
    chart_y0 = y0 + (30 if title else 10)
    chart_h  = h - (55 if title else 30)
    chart_w  = w - 50
    chart_x0 = x0 + 30

    colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED, ACCENT_PURP]
    all_v = [v for s in series.values() for v in s]
    min_v = min(all_v) - 5
    max_v = max(all_v) + 5
    rng   = max_v - min_v or 1

    n = len(labels)
    step = chart_w / max(n - 1, 1)

    # grid
    for gi in range(5):
        gy = chart_y0 + int(chart_h * gi / 4)
        canvas.create_line(chart_x0, gy, chart_x0 + chart_w, gy,
                            fill=BORDER, dash=(2, 4))
        gv = max_v - (max_v - min_v) * gi / 4
        canvas.create_text(chart_x0 - 4, gy, text=f"{gv:.0f}",
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="e")

    for xi, lbl in enumerate(labels):
        px = chart_x0 + xi * step
        canvas.create_text(px, chart_y0 + chart_h + 8,
                            text=lbl, fill=TEXT_MUTED,
                            font=FONT_SMALL, anchor="n")

    for ci, (name, vals) in enumerate(series.items()):
        col = colors[ci % len(colors)]
        pts = []
        for xi, v in enumerate(vals):
            px = chart_x0 + xi * step
            py = chart_y0 + chart_h - int((v - min_v) / rng * chart_h)
            pts.append((px, py))
        for i in range(len(pts) - 1):
            canvas.create_line(pts[i][0], pts[i][1],
                                pts[i+1][0], pts[i+1][1],
                                fill=col, width=2, smooth=True)
        for px, py in pts:
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3,
                                fill=col, outline=BG_CARD)
        # legend
        lx = chart_x0 + chart_w + 6
        ly = chart_y0 + ci * 18
        canvas.create_rectangle(lx, ly + 4, lx + 12, ly + 12, fill=col, outline="")
        canvas.create_text(lx + 15, ly + 8, text=name,
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="w")


def draw_donut(canvas, cx, cy, r, segments, labels, colors):
    start = -90.0
    for i, (val, col) in enumerate(zip(segments, colors)):
        extent = val * 3.6
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                           start=start, extent=extent,
                           fill=col, outline=BG_CARD, width=2, style="pieslice")
        mid_angle = math.radians(start + extent / 2)
        tx = cx + (r + 14) * math.cos(mid_angle)
        ty = cy + (r + 14) * math.sin(mid_angle)
        canvas.create_text(tx, ty, text=f"{val}%",
                            fill=TEXT_PRIMARY, font=FONT_SMALL, anchor="center")
        start += extent
    canvas.create_oval(cx - r * 0.6, cy - r * 0.6,
                       cx + r * 0.6, cy + r * 0.6,
                       fill=BG_CARD, outline=BG_CARD)
    # legend
    for i, (lbl, col) in enumerate(zip(labels, colors)):
        lx = cx - r
        ly = cy + r + 12 + i * 16
        canvas.create_rectangle(lx, ly, lx + 10, ly + 10, fill=col, outline="")
        canvas.create_text(lx + 14, ly + 5, text=lbl,
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="w")


def draw_progress_bar(canvas, x, y, w, h, pct, color=ACCENT_BLUE, label="", value=""):
    canvas.create_rectangle(x, y, x + w, y + h,
                             fill=BORDER, outline="", width=0)
    fill_w = int(w * pct / 100)
    if fill_w > 0:
        canvas.create_rectangle(x, y, x + fill_w, y + h,
                                 fill=color, outline="", width=0)
    if label:
        canvas.create_text(x, y - 4, text=label,
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="sw")
    if value:
        canvas.create_text(x + w, y + h // 2, text=value,
                            fill=TEXT_PRIMARY, font=FONT_SMALL, anchor="w")


# ── Main App ────────────────────────────────────────────────────────────────────

class EduDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("РАЙОНО — Аналітична панель якості освіти")
        self.configure(bg=BG_DARK)
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.resizable(True, True)

        self.current_page = tk.StringVar(value="overview")
        self.selected_school = tk.StringVar(value=SCHOOLS[0])
        self.selected_year = tk.IntVar(value=2025)
        self.selected_subject = tk.StringVar(value=SUBJECTS_NMT[0])

        self._build_layout()
        self._show_page("overview")

    # ── Layout ──────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR, height=80)
        logo_frame.pack(fill="x", padx=16, pady=(20, 8))
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="🏫 РАЙОНО", bg=BG_SIDEBAR,
                 fg=ACCENT_BLUE, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(logo_frame, text="Моніторинг якості освіти",
                 bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=12, pady=4)

        # Nav items
        nav_items = [
            ("overview",     "📊",  "Огляд"),
            ("nmt",          "📝",  "НМТ та успішність"),
            ("attendance",   "📅",  "Відвідуваність"),
            ("staff",        "👩‍🏫", "Кадри"),
            ("schools",      "🏫",  "Порівняння шкіл"),
        ]
        self.nav_btns = {}
        for key, icon, label in nav_items:
            btn = tk.Button(
                self.sidebar, text=f"  {icon}  {label}",
                bg=BG_SIDEBAR, fg=TEXT_MUTED,
                font=FONT_NAV, relief="flat", anchor="w",
                padx=12, pady=8, cursor="hand2",
                activebackground=HOVER, activeforeground=TEXT_PRIMARY,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_btns[key] = btn

        # Sidebar filter panel
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=12, pady=8)
        tk.Label(self.sidebar, text="ФІЛЬТРИ", bg=BG_SIDEBAR,
                 fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", padx=20)

        tk.Label(self.sidebar, text="Школа:", bg=BG_SIDEBAR,
                 fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6, 0))
        school_cb = ttk.Combobox(self.sidebar, textvariable=self.selected_school,
                                  values=SCHOOLS, state="readonly", width=22)
        school_cb.pack(padx=20, fill="x")
        school_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(self.sidebar, text="Рік:", bg=BG_SIDEBAR,
                 fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6, 0))
        year_cb = ttk.Combobox(self.sidebar, textvariable=self.selected_year,
                                values=YEARS, state="readonly", width=10)
        year_cb.pack(padx=20, fill="x")
        year_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(self.sidebar, text="Предмет НМТ:", bg=BG_SIDEBAR,
                 fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6, 0))
        subj_cb = ttk.Combobox(self.sidebar, textvariable=self.selected_subject,
                                values=SUBJECTS_NMT, state="readonly", width=18)
        subj_cb.pack(padx=20, fill="x")
        subj_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Bottom timestamp
        tk.Label(self.sidebar,
                 text=f"Оновлено:\n{datetime.now().strftime('%d.%m.%Y %H:%M')}",
                 bg=BG_SIDEBAR, fg=TEXT_MUTED, font=FONT_SMALL).pack(
                     side="bottom", pady=16, padx=20)

        # Main content
        self.main = tk.Frame(self, bg=BG_DARK)
        self.main.pack(side="left", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(self.main, bg=BG_CARD, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.page_title_lbl = tk.Label(
            topbar, text="Огляд", bg=BG_CARD,
            fg=TEXT_PRIMARY, font=FONT_HEADER)
        self.page_title_lbl.pack(side="left", padx=24, pady=8)

        # Refresh button
        tk.Button(topbar, text="⟳  Оновити дані",
                  bg=ACCENT_BLUE, fg="white", font=FONT_LABEL,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._refresh).pack(side="right", padx=16, pady=10)

        # Scrollable content area
        self.canvas_scroll = tk.Canvas(self.main, bg=BG_DARK,
                                        highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main, orient="vertical",
                                        command=self.canvas_scroll.yview)
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas_scroll.pack(fill="both", expand=True)

        self.content_frame = tk.Frame(self.canvas_scroll, bg=BG_DARK)
        self.content_window = self.canvas_scroll.create_window(
            (0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas_scroll.bind("<Configure>", self._on_canvas_configure)
        self.canvas_scroll.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas_scroll.bind("<Button-4>",   self._on_mousewheel)
        self.canvas_scroll.bind("<Button-5>",   self._on_mousewheel)

    def _on_frame_configure(self, e):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas_scroll.itemconfig(self.content_window, width=e.width)

    def _on_mousewheel(self, e):
        if e.num == 4:
            self.canvas_scroll.yview_scroll(-1, "units")
        elif e.num == 5:
            self.canvas_scroll.yview_scroll(1, "units")
        else:
            self.canvas_scroll.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── Navigation ──────────────────────────────────────────────────────────────

    def _show_page(self, key):
        self.current_page.set(key)
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.config(bg=HOVER, fg=TEXT_PRIMARY)
            else:
                btn.config(bg=BG_SIDEBAR, fg=TEXT_MUTED)
        self._refresh()

    def _refresh(self):
        page = self.current_page.get()
        titles = {
            "overview":   "Загальний огляд",
            "nmt":        "НМТ та успішність учнів",
            "attendance": "Відвідуваність",
            "staff":      "Кадрова статистика",
            "schools":    "Порівняння шкіл",
        }
        self.page_title_lbl.config(text=titles.get(page, ""))

        for w in self.content_frame.winfo_children():
            w.destroy()
        self.canvas_scroll.yview_moveto(0)

        {
            "overview":   self._page_overview,
            "nmt":        self._page_nmt,
            "attendance": self._page_attendance,
            "staff":      self._page_staff,
            "schools":    self._page_schools,
        }[page]()

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _kpi_card(self, parent, label, value, unit="", delta=None,
                  color=ACCENT_BLUE, w=200, h=120):
        f = tk.Frame(parent, bg=BG_CARD, width=w, height=h)
        f.pack_propagate(False)
        tk.Frame(f, bg=color, width=4, height=h).pack(side="left")
        inner = tk.Frame(f, bg=BG_CARD, padx=14, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=label, bg=BG_CARD,
                 fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")
        val_frame = tk.Frame(inner, bg=BG_CARD)
        val_frame.pack(anchor="w")
        tk.Label(val_frame, text=str(value), bg=BG_CARD,
                 fg=TEXT_PRIMARY, font=FONT_KPINUM).pack(side="left")
        if unit:
            tk.Label(val_frame, text=" " + unit, bg=BG_CARD,
                     fg=TEXT_MUTED, font=FONT_LABEL).pack(side="left", padx=(2, 0))
        if delta is not None:
            dc = ACCENT_GREEN if delta >= 0 else ACCENT_RED
            ds = f"▲ +{delta}" if delta >= 0 else f"▼ {delta}"
            tk.Label(inner, text=ds, bg=BG_CARD,
                     fg=dc, font=FONT_SMALL).pack(anchor="w")
        return f

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_TITLE,
                 padx=0, pady=0).pack(anchor="w", padx=20, pady=(18, 4))

    # ── Page: Overview ──────────────────────────────────────────────────────────

    def _page_overview(self):
        school = self.selected_school.get()
        year   = self.selected_year.get()
        subj   = self.selected_subject.get()
        pad    = tk.Frame(self.content_frame, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=16)

        # ── KPI Row ──
        kpi_row = tk.Frame(pad, bg=BG_DARK)
        kpi_row.pack(fill="x")

        avg_nmt = int(sum(nmt_score(school, year, s) for s in SUBJECTS_NMT) / len(SUBJECTS_NMT))
        avg_prev = int(sum(nmt_score(school, year - 1, s) for s in SUBJECTS_NMT) / len(SUBJECTS_NMT))
        delta_nmt = avg_nmt - avg_prev

        months = list(range(9, 13)) + list(range(1, 7))
        avg_att = round(sum(attendance_rate(school, m) for m in months) / len(months), 1)

        total_t, norm, over, vac = teacher_load(school)
        exc, good, sat, poor = grade_distribution(school)
        drops = dropout_count(school)

        kpis = [
            ("Середній бал НМТ", avg_nmt, "/200", delta_nmt, ACCENT_BLUE),
            ("Відвідуваність",   f"{avg_att}", "%", None, ACCENT_GREEN),
            ("Вчителів загалом", total_t, "осіб", None, ACCENT_PURP),
            ("Відмінники",       exc, "%", None, ACCENT_AMBER),
            ("Відрахованих",     drops, "учнів", None, ACCENT_RED),
        ]
        for label, val, unit, delta, col in kpis:
            c = self._kpi_card(kpi_row, label, val, unit, delta, col, w=200, h=120)
            c.pack(side="left", padx=(0, 12))

        # ── Row 2: NMT Bar + Attendance Line ──
        self._section_title(pad, "НМТ по предметах")
        row2 = tk.Frame(pad, bg=BG_DARK)
        row2.pack(fill="x")

        c1 = tk.Canvas(row2, width=520, height=260,
                        bg=BG_CARD, highlightthickness=0)
        c1.pack(side="left", padx=(0, 12))
        scores = [nmt_score(school, year, s) for s in SUBJECTS_NMT]
        short  = ["Мат", "Укр.м", "Англ", "Іст", "Біол"]
        draw_bar_chart(c1, scores, short,
                       f"Середній бал НМТ — {year}", 10, 0, 500, 250,
                       ACCENT_BLUE)

        c2 = tk.Canvas(row2, width=520, height=260,
                        bg=BG_CARD, highlightthickness=0)
        c2.pack(side="left")
        months_lbl = ["Вер","Жов","Лис","Гру","Січ","Лют","Бер","Кві","Тра","Чер"]
        att_vals = [attendance_rate(school, m) for m in (list(range(9,13)) + list(range(1,7)))]
        draw_line_chart(c2, {school[:10]: att_vals}, months_lbl,
                        10, 0, 500, 250, "Відвідуваність по місяцях (%)")

        # ── Row 3: Grade Donut + Teacher bar ──
        self._section_title(pad, "Успішність та кадри")
        row3 = tk.Frame(pad, bg=BG_DARK)
        row3.pack(fill="x")

        c3 = tk.Canvas(row3, width=320, height=280,
                        bg=BG_CARD, highlightthickness=0)
        c3.pack(side="left", padx=(0, 12))
        c3.create_text(160, 16, text="Розподіл успішності",
                       fill=TEXT_PRIMARY, font=FONT_TITLE, anchor="center")
        draw_donut(c3, 140, 130, 70,
                   [exc, good, sat, max(0, 100 - exc - good - sat)],
                   ["Відмінно", "Добре", "Задовільно", "Незадовільно"],
                   [ACCENT_GREEN, ACCENT_BLUE, ACCENT_AMBER, ACCENT_RED])

        c4 = tk.Canvas(row3, width=480, height=280,
                        bg=BG_CARD, highlightthickness=0)
        c4.pack(side="left")
        c4.create_text(240, 16, text="Навантаження вчителів",
                       fill=TEXT_PRIMARY, font=FONT_TITLE, anchor="center")
        cats = [("Нормальне навантаження", norm, ACCENT_GREEN),
                ("Перевантажені (>24 год)", over, ACCENT_AMBER),
                ("Вакантні посади",         vac,  ACCENT_RED)]
        for idx, (lbl, cnt, col) in enumerate(cats):
            pct = int(cnt / total_t * 100) if total_t else 0
            draw_progress_bar(c4, 30, 55 + idx * 60, 400, 18,
                               pct, col, lbl, f"{cnt} осіб ({pct}%)")

    # ── Page: NMT ───────────────────────────────────────────────────────────────

    def _page_nmt(self):
        school = self.selected_school.get()
        year   = self.selected_year.get()
        pad    = tk.Frame(self.content_frame, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=16)

        self._section_title(pad, "Динаміка НМТ — всі предмети (2021–2025)")
        c1 = tk.Canvas(pad, width=960, height=300,
                        bg=BG_CARD, highlightthickness=0)
        c1.pack()
        series = {s: [nmt_score(school, y, s) for y in YEARS] for s in SUBJECTS_NMT}
        draw_line_chart(c1, series, [str(y) for y in YEARS],
                        10, 0, 940, 290, "")

        self._section_title(pad, f"Порівняння шкіл по предмету: {self.selected_subject.get()} ({year})")
        c2 = tk.Canvas(pad, width=960, height=280,
                        bg=BG_CARD, highlightthickness=0)
        c2.pack()
        subj   = self.selected_subject.get()
        scores = [nmt_score(s, year, subj) for s in SCHOOLS]
        short  = [s.split()[1] if len(s.split()) > 1 else s[:6] for s in SCHOOLS]
        draw_bar_chart(c2, scores, short,
                       f"{subj} — {year}", 10, 0, 940, 260,
                       ACCENT_GREEN)

        self._section_title(pad, "Топ-3 та аутсайдери")
        row = tk.Frame(pad, bg=BG_DARK)
        row.pack(fill="x")
        ranked = sorted(zip(SCHOOLS, scores), key=lambda x: x[1], reverse=True)
        for i, (sc, sc_val) in enumerate(ranked):
            col = ACCENT_GREEN if i < 3 else (ACCENT_RED if i >= len(ranked) - 2 else TEXT_MUTED)
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
            f = tk.Frame(row, bg=BG_CARD, padx=14, pady=10)
            f.pack(side="left", padx=(0, 8), fill="y")
            tk.Label(f, text=medal, bg=BG_CARD,
                     fg=col, font=("Segoe UI", 18)).pack()
            tk.Label(f, text=sc[:18], bg=BG_CARD,
                     fg=TEXT_PRIMARY, font=FONT_SMALL,
                     wraplength=120).pack()
            tk.Label(f, text=str(sc_val), bg=BG_CARD,
                     fg=col, font=FONT_TITLE).pack()

    # ── Page: Attendance ────────────────────────────────────────────────────────

    def _page_attendance(self):
        school = self.selected_school.get()
        pad    = tk.Frame(self.content_frame, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=16)

        months_lbl = ["Вер","Жов","Лис","Гру","Січ","Лют","Бер","Кві","Тра","Чер"]
        months_num = list(range(9, 13)) + list(range(1, 7))

        self._section_title(pad, "Відвідуваність: поточна школа по місяцях")
        c1 = tk.Canvas(pad, width=960, height=280,
                        bg=BG_CARD, highlightthickness=0)
        c1.pack()
        vals = [attendance_rate(school, m) for m in months_num]
        colors_bar = [ACCENT_GREEN if v >= 95 else ACCENT_AMBER if v >= 90 else ACCENT_RED
                      for v in vals]
        # manual coloured bars
        w_chart, h_chart = 920, 240
        c1.create_text(480, 16, text=f"Відвідуваність — {school}",
                       fill=TEXT_PRIMARY, font=FONT_TITLE, anchor="center")
        bw = w_chart // len(vals) - 8
        for i, (v, col) in enumerate(zip(vals, colors_bar)):
            bx = 30 + i * (bw + 8)
            bh = int((v - 80) / 20 * 180)
            by = 240 - bh
            c1.create_rectangle(bx, by, bx + bw, 240,
                                  fill=col, outline="")
            c1.create_text(bx + bw // 2, by - 6, text=f"{v}%",
                            fill=TEXT_PRIMARY, font=FONT_SMALL, anchor="s")
            c1.create_text(bx + bw // 2, 252, text=months_lbl[i],
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="n")

        self._section_title(pad, "Порівняння відвідуваності: всі школи")
        c2 = tk.Canvas(pad, width=960, height=300,
                        bg=BG_CARD, highlightthickness=0)
        c2.pack()
        series = {s[:12]: [attendance_rate(s, m) for m in months_num] for s in SCHOOLS}
        draw_line_chart(c2, series, months_lbl, 10, 0, 940, 290)

        self._section_title(pad, "Середня відвідуваність по школах")
        kpi_row = tk.Frame(pad, bg=BG_DARK)
        kpi_row.pack(fill="x")
        for sc in SCHOOLS:
            avg = round(sum(attendance_rate(sc, m) for m in months_num) / len(months_num), 1)
            col = ACCENT_GREEN if avg >= 95 else ACCENT_AMBER if avg >= 92 else ACCENT_RED
            c = self._kpi_card(kpi_row, sc[:16], f"{avg}", "%", None, col, w=168, h=100)
            c.pack(side="left", padx=(0, 8))

    # ── Page: Staff ─────────────────────────────────────────────────────────────

    def _page_staff(self):
        pad = tk.Frame(self.content_frame, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=16)

        self._section_title(pad, "Кадрова статистика всіх шкіл")

        # Summary KPIs
        kpi_row = tk.Frame(pad, bg=BG_DARK)
        kpi_row.pack(fill="x")
        totals = [teacher_load(s) for s in SCHOOLS]
        total_all    = sum(t[0] for t in totals)
        overload_all = sum(t[2] for t in totals)
        vacant_all   = sum(t[3] for t in totals)

        kpis = [
            ("Вчителів всього",    total_all,    "осіб", ACCENT_BLUE),
            ("Перевантажених",     overload_all, "осіб", ACCENT_AMBER),
            ("Вакантних посад",    vacant_all,   "місць", ACCENT_RED),
        ]
        for lbl, val, unit, col in kpis:
            c = self._kpi_card(kpi_row, lbl, val, unit, None, col, w=220, h=120)
            c.pack(side="left", padx=(0, 12))

        # Per-school breakdown
        self._section_title(pad, "Розподіл навантаження по школах")
        c1 = tk.Canvas(pad, width=960, height=360,
                        bg=BG_CARD, highlightthickness=0)
        c1.pack()
        c1.create_text(480, 16, text="Навантаження вчителів по школах",
                       fill=TEXT_PRIMARY, font=FONT_TITLE, anchor="center")
        row_h = 36
        for idx, sc in enumerate(SCHOOLS):
            total, norm, over, vac = teacher_load(sc)
            y = 40 + idx * row_h
            c1.create_text(10, y + 10, text=sc[:22],
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="w")
            bar_x, bar_w = 210, 620
            norm_w = int(bar_w * norm / total)
            over_w = int(bar_w * over / total)
            vac_w  = bar_w - norm_w - over_w

            c1.create_rectangle(bar_x, y + 2, bar_x + norm_w, y + 22,
                                  fill=ACCENT_GREEN, outline="")
            c1.create_rectangle(bar_x + norm_w, y + 2,
                                  bar_x + norm_w + over_w, y + 22,
                                  fill=ACCENT_AMBER, outline="")
            c1.create_rectangle(bar_x + norm_w + over_w, y + 2,
                                  bar_x + bar_w, y + 22,
                                  fill=ACCENT_RED, outline="")
            c1.create_text(bar_x + bar_w + 8, y + 12,
                            text=f"{total} осіб",
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="w")

        # Legend
        legend_x = 840
        for i, (lbl, col) in enumerate([("Норма", ACCENT_GREEN),
                                          ("Перевантаж.", ACCENT_AMBER),
                                          ("Вакансії", ACCENT_RED)]):
            lx = legend_x
            ly = 40 + i * 22
            c1.create_rectangle(lx, ly, lx + 12, ly + 12, fill=col, outline="")
            c1.create_text(lx + 16, ly + 6, text=lbl,
                            fill=TEXT_MUTED, font=FONT_SMALL, anchor="w")

    # ── Page: Schools comparison ─────────────────────────────────────────────

    def _page_schools(self):
        year   = self.selected_year.get()
        pad    = tk.Frame(self.content_frame, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=16)

        self._section_title(pad, f"Зведена таблиця показників шкіл — {year}")

        # Build table
        cols = ["Школа", "НМТ сер.", "Відвідув.%",
                "Вчителів", "Відмінники%", "Відраховані"]
        col_w = [260, 90, 110, 100, 120, 110]
        header_h, row_h = 36, 34

        table_w = sum(col_w) + 20
        n_rows  = len(SCHOOLS)
        table_h = header_h + n_rows * row_h + 20

        c = tk.Canvas(pad, width=table_w, height=table_h,
                      bg=BG_CARD, highlightthickness=0)
        c.pack()

        # Header
        x = 10
        for ci, (col, cw) in enumerate(zip(cols, col_w)):
            c.create_rectangle(x, 0, x + cw, header_h,
                                fill=HOVER, outline=BORDER)
            c.create_text(x + cw // 2, header_h // 2,
                           text=col, fill=TEXT_PRIMARY,
                           font=FONT_LABEL, anchor="center")
            x += cw

        # Data rows
        months_num = list(range(9, 13)) + list(range(1, 7))
        all_nmt, all_att = [], []
        rows_data = []
        for sc in SCHOOLS:
            avg_nmt = int(sum(nmt_score(sc, year, s) for s in SUBJECTS_NMT) / len(SUBJECTS_NMT))
            avg_att = round(sum(attendance_rate(sc, m) for m in months_num) / len(months_num), 1)
            total_t, *_ = teacher_load(sc)
            exc, *_ = grade_distribution(sc)
            drops = dropout_count(sc)
            rows_data.append((sc, avg_nmt, avg_att, total_t, exc, drops))
            all_nmt.append(avg_nmt)
            all_att.append(avg_att)

        best_nmt = max(all_nmt)
        best_att = max(all_att)

        for ri, row in enumerate(rows_data):
            sc, avg_nmt, avg_att, total_t, exc, drops = row
            y0 = header_h + ri * row_h
            bg = BG_CARD if ri % 2 == 0 else HOVER
            x = 10
            for ci, (val, cw) in enumerate(zip(row, col_w)):
                c.create_rectangle(x, y0, x + cw, y0 + row_h,
                                    fill=bg, outline=BORDER)
                fg = TEXT_PRIMARY
                if ci == 1 and avg_nmt == best_nmt:
                    fg = ACCENT_GREEN
                elif ci == 2 and avg_att == best_att:
                    fg = ACCENT_GREEN
                elif ci == 5 and drops >= 5:
                    fg = ACCENT_RED
                c.create_text(x + cw // 2, y0 + row_h // 2,
                               text=str(val)[:22],
                               fill=fg, font=FONT_SMALL, anchor="center")
                x += cw

        # Radar-style comparison (simplified)
        self._section_title(pad, "Рейтинг шкіл (інтегральний індекс)")
        c2 = tk.Canvas(pad, width=960, height=260,
                        bg=BG_CARD, highlightthickness=0)
        c2.pack()

        # Compute composite index 0–100
        def composite(sc):
            avg_nmt = int(sum(nmt_score(sc, year, s) for s in SUBJECTS_NMT) / len(SUBJECTS_NMT))
            avg_att = round(sum(attendance_rate(sc, m) for m in months_num) / len(months_num), 1)
            exc, *_ = grade_distribution(sc)
            drops = dropout_count(sc)
            nmt_n = (avg_nmt - 100) / 100 * 40
            att_n = (avg_att - 85) / 15 * 30
            exc_n = exc / 30 * 20
            drop_n = max(0, 10 - drops)
            return min(100, round(nmt_n + att_n + exc_n + drop_n, 1))

        composites = [(sc, composite(sc)) for sc in SCHOOLS]
        composites.sort(key=lambda x: x[1], reverse=True)
        names  = [x[0].split()[1][:10] if len(x[0].split()) > 1 else x[0][:10] for x in composites]
        values = [x[1] for x in composites]
        draw_bar_chart(c2, values, names, "Інтегральний індекс якості освіти",
                       10, 0, 940, 250, ACCENT_PURP, "{:.1f}")


# ── Entry point ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("TCombobox",
                    fieldbackground=BG_CARD,
                    background=BG_CARD,
                    foreground=TEXT_PRIMARY,
                    arrowcolor=TEXT_MUTED,
                    bordercolor=BORDER,
                    lightcolor=BORDER,
                    darkcolor=BORDER)
    style.configure("TScrollbar",
                    background=BG_CARD,
                    troughcolor=BG_DARK,
                    arrowcolor=TEXT_MUTED,
                    bordercolor=BORDER)
    style.configure("TSeparator", background=BORDER)

    app = EduDashboard()
    app.mainloop()
