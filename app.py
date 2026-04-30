import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import calplot
import os
import json
import zipfile
import io
import random
import base64
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px

def _b64_font(filename):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts", filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

_MONACO_B64  = _b64_font("monaco.ttf")
_COURIER_B64 = _b64_font("CourierNew.ttf")

st.set_page_config(
    page_title="Life Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

_FONT_CSS = f"""
<style>
@font-face {{
    font-family: 'CourierNew';
    src: url('data:font/truetype;base64,{_COURIER_B64}') format('truetype');
    font-weight: normal; font-style: normal;
}}
@font-face {{
    font-family: 'Monaco';
    src: url('data:font/truetype;base64,{_MONACO_B64}') format('truetype');
    font-weight: normal; font-style: normal;
}}

/* ── Body: Courier New — explicit tags only, no wildcard that catches headings ── */
body, p, span, li, label, small, caption, a,
input, textarea, select, option,
.stButton > button,
.stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown a,
[data-testid="stWidgetLabel"],
[data-testid="stText"], [data-testid="stCaption"],
[data-baseweb="select"] *, [data-baseweb="input"] *,
[data-baseweb="tab"] *, [data-baseweb="tab-list"] * {{
    font-family: 'CourierNew', 'Courier New', Courier, monospace !important;
}}

/* ── Headings: Monaco — explicit class selectors beat the body rule above ── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
[data-testid="stHeading"], [data-testid="stHeadingWithActionElements"] {{
    font-family: 'Monaco', 'CourierNew', 'Courier New', Courier, monospace !important;
    letter-spacing: -0.01em;
}}
</style>"""

_LIGHT_CSS = """
<style>
[data-testid="metric-container"] {
    background: white; border: 1px solid #e5e7eb;
    border-radius: 12px; padding: 16px 20px;
}
div[data-testid="stHorizontalBlock"] > div { align-items: center; }
</style>"""

_DARK_CSS = """
<style>
[data-testid="stAppViewContainer"],
[data-testid="stMain"]  { background-color: #111827 !important; }
[data-testid="stHeader"] { background-color: #111827 !important; }
[data-testid="stSidebar"] { background-color: #1f2937 !important; }
[data-testid="stSidebar"] * { color: #e5e7eb !important; }

[data-testid="metric-container"] {
    background: #1f2937 !important; border-color: #374151 !important;
    border-radius: 12px; padding: 16px 20px;
}
[data-testid="metric-container"] * { color: #f9fafb !important; }

div[data-testid="stHorizontalBlock"] > div { align-items: center; }

p, span, li, h1, h2, h3, h4, label,
.stMarkdown *, [data-testid="stWidgetLabel"] * { color: #f9fafb !important; }
.stCaption, small { color: #9ca3af !important; }

hr { border-color: #374151 !important; }

[data-testid="stAlert"] { background-color: #1f2937 !important; }
[data-testid="stAlert"] * { color: #f9fafb !important; }

input, textarea {
    background-color: #374151 !important;
    color: #f9fafb !important; border-color: #4b5563 !important;
}
[data-baseweb="select"] > div:first-child {
    background-color: #374151 !important;
    border-color: #4b5563 !important; color: #f9fafb !important;
}
[data-baseweb="select"] span { color: #f9fafb !important; }
[data-baseweb="popover"] * { background-color: #374151 !important; color: #f9fafb !important; }
[data-baseweb="tab-list"] { background-color: #1f2937 !important; border-bottom-color: #374151 !important; }
[data-baseweb="tab"]      { color: #9ca3af !important; }
[aria-selected="true"]    { color: #22c55e !important; }

.stButton > button:not([kind="primary"]) {
    background-color: #374151 !important; border-color: #4b5563 !important; color: #f9fafb !important;
}
[data-testid="stFileUploadDropzone"] {
    background-color: #1f2937 !important; border-color: #4b5563 !important;
}
[data-testid="stDataFrame"] { filter: invert(1) hue-rotate(180deg); }
[data-testid="stNumberInput"] button { background-color: #374151 !important; color: #f9fafb !important; }
</style>"""

# Injected once at the top — reads session state before the sidebar renders
_dark = st.session_state.get("dark_mode", False)
st.markdown(_DARK_CSS if _dark else _LIGHT_CSS, unsafe_allow_html=True)
st.markdown(_FONT_CSS, unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

ARC_COLOR_MAP = {
    "Blue":   "#3b82f6",
    "Purple": "#8b5cf6",
    "Orange": "#f97316",
    "Red":    "#ef4444",
    "Pink":   "#ec4899",
    "Teal":   "#14b8a6",
    "Yellow": "#eab308",
    "Gray":   "#6b7280",
}


# ─── Paths ────────────────────────────────────────────────────────────────────

def profile_path(name):
    return os.path.join(DATA_DIR, f"{name}_profile.csv")

def diary_path(name):
    return os.path.join(DATA_DIR, f"{name}_diary.json")

def arcs_path(name):
    return os.path.join(DATA_DIR, f"{name}_arcs.json")


# ─── Core helpers ─────────────────────────────────────────────────────────────

def compute_daily_score(scores, alpha=0.5):
    valid = [float(s) for s in scores if s is not None and not np.isnan(float(s))]
    if not valid:
        return 0.0
    total = sum(np.sign(x) * (abs(x / 10) ** alpha) for x in valid)
    return float(max(0.0, total / len(valid)))


def list_profiles():
    return sorted(
        f[: -len("_profile.csv")]
        for f in os.listdir(DATA_DIR)
        if f.endswith("_profile.csv")
    )


def load_profile(name):
    path = profile_path(name)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if df.empty or "date" not in df.columns:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def get_activities(df):
    return [c[:-6] for c in df.columns if c.endswith("_score") and c != "daily_score"]


# ─── Diary ────────────────────────────────────────────────────────────────────

def load_diary(name):
    path = diary_path(name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_diary_entry(name, date_str, text):
    diary = load_diary(name)
    if text.strip():
        diary[date_str] = text.strip()
    elif date_str in diary:
        del diary[date_str]
    with open(diary_path(name), "w", encoding="utf-8") as f:
        json.dump(diary, f, ensure_ascii=False, indent=2)


# ─── Arcs ─────────────────────────────────────────────────────────────────────

def load_arcs(name):
    path = arcs_path(name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_arcs(name, arcs):
    with open(arcs_path(name), "w", encoding="utf-8") as f:
        json.dump(arcs, f, ensure_ascii=False, indent=2)


# ─── Profile mutations ────────────────────────────────────────────────────────

def save_entry(profile_name, entry_date, scores_dict, durations_dict, diary_text=""):
    date_str = entry_date.strftime("%Y-%m-%d")

    # Diary is always saved independently
    _save_diary_entry(profile_name, date_str, diary_text)

    # Only write a CSV row when at least one activity is scored
    if not scores_dict:
        return None

    path = profile_path(profile_name)
    df = pd.read_csv(path)
    activities = get_activities(df)

    new_row = {"date": date_str}
    score_values = []
    for act in activities:
        s = scores_dict.get(act)
        d = durations_dict.get(act)
        if s is not None:
            new_row[f"{act}_score"] = float(s)
            score_values.append(float(s))
        else:
            new_row[f"{act}_score"] = np.nan
        new_row[f"{act}_duration"] = float(d) if d else np.nan

    ds = compute_daily_score(score_values)
    new_row["daily_score"] = ds

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df[df["date"] != date_str]

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.sort_values("date").reset_index(drop=True).to_csv(path, index=False)
    return ds


def create_profile(name, activities):
    cols = ["date", "daily_score"]
    for act in activities:
        cols += [f"{act}_score", f"{act}_duration"]
    pd.DataFrame(columns=cols).to_csv(profile_path(name), index=False)


def add_activity(profile_name, activity_name):
    path = profile_path(profile_name)
    df = pd.read_csv(path)
    s_col = f"{activity_name}_score"
    if s_col in df.columns:
        raise ValueError(f'Activity "{activity_name}" already exists.')
    df[s_col] = np.nan
    df[f"{activity_name}_duration"] = np.nan
    df.to_csv(path, index=False)


def remove_activity(profile_name, activity_name):
    path = profile_path(profile_name)
    df = pd.read_csv(path)
    cols = [f"{activity_name}_score", f"{activity_name}_duration"]
    df = df.drop(columns=[c for c in cols if c in df.columns])
    df.to_csv(path, index=False)


# ─── Export / Import ──────────────────────────────────────────────────────────

def export_profile_zip(name):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in [
            (profile_path(name), f"{name}_profile.csv"),
            (diary_path(name),   f"{name}_diary.json"),
            (arcs_path(name),    f"{name}_arcs.json"),
        ]:
            if os.path.exists(src):
                zf.write(src, arcname)
    buf.seek(0)
    return buf


def import_profile_zip(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        for n in names:
            if ".." in n or n.startswith("/"):
                raise ValueError("Invalid zip file (path traversal detected).")

        profile_name = next(
            (n[: -len("_profile.csv")] for n in names
             if n.endswith("_profile.csv") and "/" not in n),
            None,
        )
        if not profile_name:
            raise ValueError("No profile CSV found in the zip.")

        for fname in names:
            dest = os.path.join(DATA_DIR, os.path.basename(fname))
            with zf.open(fname) as src, open(dest, "wb") as dst:
                dst.write(src.read())

    return profile_name


# ─── Arc overlay on calplot axes ─────────────────────────────────────────────

def draw_arcs_on_calendar(ax, arcs, year, fig=None):
    """
    Draw arc bars directly above the calplot calendar, date-aligned.

    calplot uses an inverted y-axis: y=0 is Monday (top), y=7 is Sunday (bottom).
    Negative y values therefore appear *above* Monday in display space.
    Week column of a date = (day_of_year + jan1_weekday) // 7  (same formula calplot uses).
    """
    from datetime import date as _date

    jan1     = _date(year, 1, 1)
    jan1_dow = jan1.weekday()          # 0 = Monday
    year_end = _date(year, 12, 31)

    def to_col(d_str):
        d = _date.fromisoformat(d_str) if isinstance(d_str, str) else d_str
        d = max(d, jan1)
        d = min(d, year_end)
        return ((d - jan1).days + jan1_dow) // 7

    n      = len(arcs)
    BAR_H  = 0.62   # height of each arc bar (in data units)
    STEP   = 0.82   # distance between bar bottoms
    GAP    = 0.28   # gap between y=0 (Monday) and the nearest bar

    # Extend the y-axis upward (more negative) to fit all bars
    ylim = ax.get_ylim()                      # e.g. (7.1, -0.1) when inverted
    new_top = -(GAP + n * STEP + 0.15)
    ax.set_ylim(ylim[0], new_top)

    # Grow the figure height proportionally so bars are not squeezed
    if fig is not None:
        old_span = ylim[0] - ylim[1]
        new_span = ylim[0] - new_top
        if old_span > 0:
            fig.set_figheight(fig.get_figheight() * new_span / old_span)

    for i, arc in enumerate(arcs):
        col_start = to_col(arc["start"])
        col_end   = to_col(arc["end"]) + 1   # +1 = include last day's column

        # Bottom of this bar in data coords (negative → above Monday)
        rect_y = -(GAP + i * STEP + BAR_H)

        ax.add_patch(plt.Rectangle(
            [col_start, rect_y], col_end - col_start, BAR_H,
            color=arc["color"], alpha=0.82, linewidth=0, clip_on=False,
        ))

        label = arc["name"] if len(arc["name"]) <= 20 else arc["name"][:18] + "…"
        ax.text(
            (col_start + col_end) / 2, rect_y + BAR_H / 2,
            label,
            ha="center", va="center",
            fontsize=8, fontweight="bold", color="white", clip_on=False,
        )


# ─── Shared chart helper ──────────────────────────────────────────────────────

def arc_timeline_fig(arcs, year_filter=None):
    dark = st.session_state.get("dark_mode", False)
    GRID = "#374151" if dark else "#f3f4f6"
    BG   = "#1f2937" if dark else "white"
    FC   = "#f9fafb" if dark else "#111827"

    visible = arcs
    if year_filter is not None:
        y0, y1 = f"{year_filter}-01-01", f"{year_filter}-12-31"
        visible = [a for a in arcs if a["end"] >= y0 and a["start"] <= y1]
    if not visible:
        return None

    arc_df = pd.DataFrame([
        {"Arc": a["name"], "Start": a["start"], "Finish": a["end"]}
        for a in visible
    ])
    color_map = {a["name"]: a["color"] for a in visible}

    fig = px.timeline(arc_df, x_start="Start", x_end="Finish", y="Arc",
                      color="Arc", color_discrete_map=color_map)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=max(80, len(visible) * 44 + 60),
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color=FC),
        xaxis=dict(showgrid=True, gridcolor=GRID),
    )
    return fig


def add_arcs_to_fig(fig, arcs):
    for arc in arcs:
        fig.add_vrect(
            x0=arc["start"], x1=arc["end"],
            fillcolor=arc["color"], opacity=0.08,
            layer="below", line_width=0,
            annotation_text=arc["name"],
            annotation_position="top left",
            annotation_font_size=11,
        )


# ─── Pages ────────────────────────────────────────────────────────────────────

def page_dashboard(profile_name):
    df = load_profile(profile_name)

    if df is None or df.empty:
        st.info("No entries yet — go to **📝 Add Entry** to start tracking!")
        return

    activities = get_activities(df)
    valid = df.dropna(subset=["daily_score"])
    if valid.empty:
        st.info("No scored entries yet.")
        return

    # ── Stats ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    streak = 0
    dates_set = set(valid["date"].dt.strftime("%Y-%m-%d"))
    d = date.today()
    while d.strftime("%Y-%m-%d") in dates_set:
        streak += 1
        d -= timedelta(days=1)

    best_idx   = valid["daily_score"].idxmax()
    best_score = valid.loc[best_idx, "daily_score"]
    best_date  = valid.loc[best_idx, "date"].strftime("%b %d")
    avg_score  = valid["daily_score"].mean()
    last_score = valid.sort_values("date").iloc[-1]["daily_score"]

    c1.metric("Total Entries", len(valid))
    c2.metric("Average Score", f"{avg_score:.3f}",
              delta=f"{last_score - avg_score:+.3f} last vs avg")
    c3.metric("🔥 Streak", f"{streak} days")
    c4.metric("Best Day", f"{best_score:.3f}", delta=best_date, delta_color="off")

    st.divider()

    # ── Calendar heatmap ───────────────────────────────────────────────────
    st.subheader("📅 Year Overview")

    years    = sorted(df["date"].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("Year", years, index=0, key="year_sel")

    df_year = (
        df[df["date"].dt.year == sel_year].copy().set_index("date")
    )
    df_year["daily_score"] = df_year["daily_score"].fillna(0)
    series = df_year["daily_score"]

    if series.sum() > 0:
        try:
            dark = st.session_state.get("dark_mode", False)
            fig_cal, _ = calplot.calplot(
                series, cmap="RdYlGn", vmin=0, vmax=1,
                fillcolor="#374151" if dark else "#eeeeee",
                linewidth=0.5, figsize=(18, 3.5),
                yearlabel_kws={"fontsize": 14, "color": "#9ca3af" if dark else "#333333"},
            )
            if dark:
                fig_cal.patch.set_facecolor("#111827")
                for _ax in fig_cal.axes:
                    _ax.set_facecolor("#111827")
                    for _t in _ax.get_xticklabels() + _ax.get_yticklabels():
                        _t.set_color("#9ca3af")
            st.pyplot(fig_cal)
            plt.close(fig_cal)
        except Exception as e:
            st.warning(f"Could not render heatmap: {e}")
    else:
        st.info(f"No entries for {sel_year}.")

    # Arc timeline below the heatmap
    arcs    = load_arcs(profile_name)
    arc_fig = arc_timeline_fig(arcs, year_filter=sel_year)
    if arc_fig:
        st.plotly_chart(arc_fig, use_container_width=True)

    st.divider()

    # ── Recent entries ─────────────────────────────────────────────────────
    st.subheader("🗓️ Recent Entries")
    diary = load_diary(profile_name)

    recent = valid.sort_values("date", ascending=False).head(10).copy()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    recent["daily_score"] = recent["daily_score"].round(3)
    recent["📖"] = recent["date"].apply(
        lambda d: (diary.get(d, "")[:70] + "…") if len(diary.get(d, "")) > 70
                  else diary.get(d, "")
    )

    show_cols = ["date", "daily_score", "📖"] + [f"{a}_score" for a in activities[:4]]
    show_cols = [c for c in show_cols if c in recent.columns]

    st.dataframe(
        recent[show_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "daily_score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=1, format="%.3f"
            ),
            "📖": st.column_config.TextColumn("Diary", width="medium"),
        },
    )


def page_add_entry(profile_name):
    df = load_profile(profile_name)
    if df is None:
        st.error("Profile not found.")
        return

    activities = get_activities(df)
    diary      = load_diary(profile_name)

    col_date, col_preview = st.columns([3, 1])
    with col_date:
        entry_date = st.date_input("📆 Date", value=date.today())
    preview_slot = col_preview.empty()

    date_str = entry_date.strftime("%Y-%m-%d")
    existing = None
    if not df.empty:
        match = df[df["date"].dt.strftime("%Y-%m-%d") == date_str]
        if not match.empty:
            existing = match.iloc[0]
            st.caption(f"✏️ Editing existing entry for **{date_str}**")

    st.divider()

    def ex_val(col):
        if existing is None:
            return None
        val = existing.get(col)
        return None if val is None or (isinstance(val, float) and np.isnan(val)) else float(val)

    # Column headers
    _, hn, hs, hv, hd = st.columns([0.5, 1.5, 3.5, 0.8, 1.8])
    hn.caption("**Activity**")
    hs.caption("**Score** (−10 → 10)")
    hd.caption("**Duration (min)**")

    scores_dict    = {}
    durations_dict = {}

    for act in activities:
        ex_score = ex_val(f"{act}_score")
        ex_dur   = ex_val(f"{act}_duration")

        c_cb, c_name, c_slider, c_val, c_dur = st.columns([0.5, 1.5, 3.5, 0.8, 1.8])

        with c_cb:
            done = st.checkbox("", key=f"cb_{act}", value=(ex_score is not None))

        with c_name:
            color = "#111827" if done else "#9ca3af"
            st.markdown(
                f"<p style='margin-top:6px;font-weight:500;color:{color}'>"
                f"{act.capitalize()}</p>",
                unsafe_allow_html=True,
            )

        with c_slider:
            score_val = st.slider(
                "", min_value=-10.0, max_value=10.0,
                value=ex_score if ex_score is not None else 0.0,
                step=0.5, key=f"sl_{act}",
                disabled=not done, label_visibility="collapsed",
            )

        with c_val:
            if done:
                sc = "#16a34a" if score_val > 0 else ("#ef4444" if score_val < 0 else "#6b7280")
                st.markdown(
                    f"<p style='margin-top:6px;font-weight:700;color:{sc};"
                    f"text-align:center'>{score_val:+.1f}</p>",
                    unsafe_allow_html=True,
                )

        with c_dur:
            dur_val = st.number_input(
                "", min_value=0, max_value=1440,
                value=int(ex_dur) if ex_dur is not None else 0,
                key=f"dur_{act}",
                disabled=not done, label_visibility="collapsed",
            )

        if done:
            scores_dict[act] = score_val
            if dur_val > 0:
                durations_dict[act] = dur_val

    preview = compute_daily_score(list(scores_dict.values()))
    with preview_slot.container():
        st.metric("Preview", f"{preview:.3f}" if scores_dict else "—")

    st.divider()

    # ── Diary ──────────────────────────────────────────────────────────────
    st.subheader("📖 Diary")
    diary_text = st.text_area(
        "diary",
        value=diary.get(date_str, ""),
        height=160,
        key=f"diary_{date_str}",
        label_visibility="collapsed",
        placeholder="What happened today?",
    )

    st.divider()

    save_col, _ = st.columns([2, 4])
    with save_col:
        if st.button("💾 Save Entry", type="primary", use_container_width=True):
            if not scores_dict and not diary_text.strip():
                st.warning("Check at least one activity or write a diary entry.")
            else:
                ds = save_entry(
                    profile_name, entry_date,
                    scores_dict, durations_dict, diary_text,
                )
                if ds is not None:
                    st.success(f"✅ Saved! Daily score: **{ds:.3f}**")
                else:
                    st.success("✅ Diary entry saved!")
                st.balloons()


def page_charts(profile_name):
    df = load_profile(profile_name)
    if df is None or df.empty:
        st.info("No data to chart yet.")
        return

    activities = get_activities(df)
    arcs       = load_arcs(profile_name)

    c1, c2, c3 = st.columns([3, 1, 2])
    with c1:
        selected = st.multiselect(
            "Activities", activities,
            default=activities[: min(3, len(activities))],
        )
    with c2:
        freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
    with c3:
        min_d = df["date"].min().date()
        max_d = df["date"].max().date()
        dr    = st.date_input("Date range", value=(min_d, max_d), key="charts_dr")

    if len(dr) == 2:
        range_start, range_end = dr[0], dr[1]
        df_f = df[
            (df["date"] >= pd.Timestamp(range_start)) &
            (df["date"] <= pd.Timestamp(range_end))
        ].copy()
    else:
        df_f = df.copy()
        range_start = df_f["date"].min().date()
        range_end   = df_f["date"].max().date()

    if df_f.empty:
        st.warning("No data in selected range.")
        return

    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
    df_f = df_f.set_index("date")
    if freq == "Daily":
        all_dates = pd.date_range(range_start, range_end, freq="D")
        df_f = df_f.reindex(all_dates)
        df_f.index.name = "date"
    else:
        df_f = df_f.resample(freq_map[freq]).mean(numeric_only=True)
    df_f = df_f.reset_index()

    dark   = st.session_state.get("dark_mode", False)
    BG     = "#1f2937" if dark else "white"
    GRID   = "#374151" if dark else "#f3f4f6"
    FCOLOR = "#f9fafb" if dark else "#111827"
    COLORS = px.colors.qualitative.Set2
    TICKFMT  = {"Daily": "%b %d", "Weekly": "%b %d '%y", "Monthly": "%b %Y"}[freq]
    XRANGE   = [range_start.isoformat(), range_end.isoformat()]
    LAYOUT = dict(
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor=BG, paper_bgcolor=BG,
        hovermode="x unified",
        font=dict(color=FCOLOR),
    )

    # Daily score — pass full df_f so NaN gaps break the line
    if df_f["daily_score"].notna().any():
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df_f["date"], y=df_f["daily_score"],
            mode="lines+markers", name="Daily Score",
            line=dict(color="#16a34a", width=2.5), marker=dict(size=5),
            fill="tozeroy" if freq == "Daily" else "none",
            fillcolor="rgba(22,163,74,0.08)",
            connectgaps=False,
        ))
        add_arcs_to_fig(fig1, arcs)
        fig1.update_layout(title="Daily Score", height=260,
                           yaxis=dict(range=[0, 1], tickformat=".2f"), **LAYOUT)
        fig1.update_xaxes(showgrid=True, gridcolor=GRID, tickformat=TICKFMT, range=XRANGE)
        fig1.update_yaxes(showgrid=True, gridcolor=GRID)
        st.plotly_chart(fig1, use_container_width=True)

    # Activity scores — same: pass full column with NaN for gaps
    if selected:
        fig2 = go.Figure()
        has_act = False
        for i, act in enumerate(selected):
            col = f"{act}_score"
            if col in df_f.columns and df_f[col].notna().any():
                fig2.add_trace(go.Scatter(
                    x=df_f["date"], y=df_f[col],
                    mode="lines+markers", name=act.capitalize(),
                    line=dict(color=COLORS[i % len(COLORS)], width=2),
                    marker=dict(size=5),
                    connectgaps=False,
                ))
                has_act = True
        if has_act:
            fig2.add_hline(y=0, line_dash="dash", line_color="#d1d5db", opacity=0.7)
            add_arcs_to_fig(fig2, arcs)
            fig2.update_layout(title="Activity Scores", height=320,
                               yaxis=dict(range=[-10, 10], title="Score"), **LAYOUT)
            fig2.update_xaxes(showgrid=True, gridcolor=GRID, tickformat=TICKFMT, range=XRANGE)
            fig2.update_yaxes(showgrid=True, gridcolor=GRID)
            st.plotly_chart(fig2, use_container_width=True)

        # Durations (bar chart — NaN bars simply vanish, no gap-line issue)
        fig3 = go.Figure()
        has_dur = False
        for i, act in enumerate(selected):
            col = f"{act}_duration"
            if col in df_f.columns and df_f[col].notna().any():
                v3 = df_f.dropna(subset=[col])
                fig3.add_trace(go.Bar(
                    x=v3["date"], y=v3[col],
                    name=act.capitalize(),
                    marker_color=COLORS[i % len(COLORS)],
                ))
                has_dur = True
        if has_dur:
            add_arcs_to_fig(fig3, arcs)
            fig3.update_layout(title="Time Spent (minutes)", height=260,
                               barmode="group", yaxis_title="Minutes", **LAYOUT)
            fig3.update_xaxes(tickformat=TICKFMT, range=XRANGE)
            st.plotly_chart(fig3, use_container_width=True)


def page_review(profile_name):
    df = load_profile(profile_name)
    if df is None or df.empty:
        st.info("No entries yet.")
        return

    diary      = load_diary(profile_name)
    activities = get_activities(df)
    dark       = st.session_state.get("dark_mode", False)

    valid = df.dropna(subset=["daily_score"]).sort_values("date", ascending=False).copy()
    if valid.empty:
        st.info("No scored entries yet.")
        return

    dates_with_data = [r["date"].date() for _, r in valid.iterrows()]

    if "review_date" not in st.session_state:
        st.session_state["review_date"] = dates_with_data[0]

    def _pick_random():
        st.session_state["review_date"] = random.choice(dates_with_data)

    def _set_review_date(d):
        st.session_state["review_date"] = d

    # ── Controls row ───────────────────────────────────────────────────────
    col_ctrl, col_list = st.columns([3, 2], gap="large")

    with col_ctrl:
        c_cal, c_rnd = st.columns([4, 1])
        with c_cal:
            st.date_input("📆 Day", key="review_date", label_visibility="visible")
        with c_rnd:
            st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
            st.button("🎲", help="Random day", use_container_width=True, on_click=_pick_random)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Day detail ─────────────────────────────────────────────────
        selected_date = st.session_state["review_date"]
        if hasattr(selected_date, "strftime"):
            date_str = selected_date.strftime("%Y-%m-%d")
        else:
            date_str = str(selected_date)

        match = valid[valid["date"].dt.strftime("%Y-%m-%d") == date_str]

        if not match.empty:
            row = match.iloc[0]
            ds  = float(row["daily_score"])
            sc  = "#16a34a" if ds >= 0.7 else ("#eab308" if ds >= 0.4 else "#ef4444")

            st.markdown(
                f"<div style='background:{sc};border-radius:16px;padding:22px 20px;"
                f"text-align:center;margin-bottom:16px'>"
                f"<p style='color:rgba(255,255,255,.8);font-size:13px;margin:0'>{date_str}</p>"
                f"<p style='color:white;font-size:44px;font-weight:700;margin:4px 0;line-height:1'>"
                f"{ds:.3f}</p>"
                f"<p style='color:rgba(255,255,255,.7);font-size:12px;margin:0'>daily score</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Activity breakdown
            border = "#374151" if dark else "#f3f4f6"
            tc     = "#f9fafb" if dark else "#111827"
            for act in activities:
                s_val = row.get(f"{act}_score")
                d_val = row.get(f"{act}_duration")
                if s_val is None or (isinstance(s_val, float) and np.isnan(s_val)):
                    continue
                s_val = float(s_val)
                sc2   = "#16a34a" if s_val > 0 else ("#ef4444" if s_val < 0 else "#6b7280")
                dur_str = ""
                if d_val is not None and not (isinstance(d_val, float) and np.isnan(d_val)):
                    dur_str = f"<span style='color:#9ca3af;font-size:12px'> · {int(d_val)} min</span>"
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:7px 0;border-bottom:1px solid {border}'>"
                    f"<span style='color:{tc}'>{act.capitalize()}{dur_str}</span>"
                    f"<span style='font-weight:700;color:{sc2};font-size:15px'>{s_val:+.1f}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Diary
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            diary_text = diary.get(date_str, "")
            if diary_text:
                st.markdown("**📖 Diary**")
                bd = "#1f2937" if dark else "#f9fafb"
                bc = "#374151" if dark else "#e5e7eb"
                st.markdown(
                    f"<div style='background:{bd};border:1px solid {bc};border-radius:10px;"
                    f"padding:16px;white-space:pre-wrap;color:{tc};font-size:14px;"
                    f"line-height:1.65;margin-top:8px'>{diary_text}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No diary entry for this day.")
        else:
            st.info("No data for the selected day — pick one from the list →")

    # ── Scrollable day list ────────────────────────────────────────────────
    with col_list:
        st.markdown(f"**{len(valid)} entries**")
        with st.container(height=580):
            for _, row in valid.iterrows():
                d     = row["date"].date()
                d_str = d.strftime("%Y-%m-%d")
                ds    = float(row["daily_score"])
                emoji = "🟢" if ds >= 0.7 else ("🟡" if ds >= 0.4 else "🔴")
                diary_text = diary.get(d_str, "")
                preview    = (diary_text[:55] + "…") if len(diary_text) > 55 else diary_text
                label      = f"{emoji}  {d_str}"
                if preview:
                    label += f"  ·  {preview}"
                is_sel = (d == st.session_state.get("review_date"))
                st.button(
                    label, key=f"rev_{d_str}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                    on_click=_set_review_date, args=(d,),
                )


def page_arcs(profile_name):
    arcs = load_arcs(profile_name)

    st.subheader("Your Arcs")

    if arcs:
        fig = arc_timeline_fig(arcs)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        to_delete = None
        for i, arc in enumerate(arcs):
            c1, c2, c3, c4 = st.columns([0.4, 2.5, 3, 1])
            with c1:
                st.markdown(
                    f"<div style='width:22px;height:22px;border-radius:4px;"
                    f"background:{arc['color']};margin-top:6px'></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**{arc['name']}**")
            with c3:
                st.caption(f"{arc['start']}  →  {arc['end']}")
            with c4:
                if st.button("Delete", key=f"del_{i}"):
                    to_delete = i

        if to_delete is not None:
            arcs.pop(to_delete)
            _save_arcs(profile_name, arcs)
            st.rerun()
    else:
        st.info("No arcs yet — create one below.")

    st.divider()
    st.subheader("➕ New Arc")

    col1, col2 = st.columns(2)
    with col1:
        arc_name = st.text_input("Name", placeholder="e.g. Summer 2026, Exam period…")
    with col2:
        arc_color_label = st.selectbox("Color", list(ARC_COLOR_MAP.keys()))
    col3, col4 = st.columns(2)
    with col3:
        arc_start = st.date_input("Start date", key="arc_start")
    with col4:
        arc_end = st.date_input("End date", key="arc_end")

    if st.button("Create Arc", type="primary"):
        if not arc_name.strip():
            st.error("Enter an arc name.")
        elif arc_end < arc_start:
            st.error("End date must be after start date.")
        else:
            arcs.append({
                "name":  arc_name.strip(),
                "start": arc_start.strftime("%Y-%m-%d"),
                "end":   arc_end.strftime("%Y-%m-%d"),
                "color": ARC_COLOR_MAP[arc_color_label],
            })
            _save_arcs(profile_name, arcs)
            st.success(f'✅ Arc "{arc_name.strip()}" created!')
            st.rerun()


def page_settings(profile_name):
    tab1, tab2, tab3 = st.tabs(["🎯 Activities", "📤 Share", "✨ New Profile"])

    # ── Activities ─────────────────────────────────────────────────────────
    with tab1:
        if profile_name is None:
            st.info("Select a profile first.")
        else:
            df = load_profile(profile_name)
            activities = get_activities(df) if df is not None else []

            st.subheader("Current activities")
            if activities:
                to_remove = None
                for act in activities:
                    c1, c2, c3 = st.columns([5, 1, 2])
                    c1.markdown(f"• **{act.capitalize()}**")
                    if c2.button("Remove", key=f"rm_{act}"):
                        to_remove = act
                    c3.caption("⚠️ all data lost")
                if to_remove:
                    remove_activity(profile_name, to_remove)
                    st.success(f'Removed "{to_remove}".')
                    st.rerun()
            else:
                st.info("No activities defined.")

            st.divider()
            st.subheader("Add activity")
            col_in, col_btn = st.columns([4, 1])
            with col_in:
                new_act = st.text_input(
                    "name", placeholder="e.g. Meditation",
                    label_visibility="collapsed", key="add_act_input",
                )
            with col_btn:
                if st.button("Add", type="primary", use_container_width=True):
                    if not new_act.strip():
                        st.error("Enter a name.")
                    else:
                        try:
                            add_activity(profile_name, new_act.strip())
                            st.success(f'✅ Added "{new_act.strip()}".')
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

    # ── Share ──────────────────────────────────────────────────────────────
    with tab2:
        if profile_name is None:
            st.info("Select a profile first.")
        else:
            st.subheader("Export")
            st.caption(
                "Download your full profile — scores, diary and arcs — as a single zip "
                "file you can send to a friend."
            )
            zip_buf = export_profile_zip(profile_name)
            st.download_button(
                label=f"⬇️ Download {profile_name}.lifecal.zip",
                data=zip_buf,
                file_name=f"{profile_name}.lifecal.zip",
                mime="application/zip",
            )

            st.divider()
            st.subheader("Import")
            st.caption("Upload a `.lifecal.zip` received from a friend.")
            uploaded = st.file_uploader(
                "Choose file", type="zip", key="import_zip",
                label_visibility="collapsed",
            )
            if uploaded is not None:
                if st.button("Import Profile", type="primary"):
                    try:
                        imported = import_profile_zip(uploaded.read())
                        st.success(f'✅ Profile "{imported}" imported!')
                        st.session_state.current_profile = imported
                        st.rerun()
                    except Exception as e:
                        st.error(f"Import failed: {e}")

    # ── New Profile ────────────────────────────────────────────────────────
    with tab3:
        name = st.text_input("Profile name", placeholder="e.g. alice", key="np_name")
        st.markdown("**Activities:**")

        if "new_acts" not in st.session_state:
            st.session_state.new_acts = [""]

        to_remove = None
        for i, val in enumerate(st.session_state.new_acts):
            c1, c2 = st.columns([8, 1])
            with c1:
                st.session_state.new_acts[i] = st.text_input(
                    f"act_{i}", value=val, key=f"na_{i}",
                    placeholder="e.g. Sport, Reading, Piano…",
                    label_visibility="collapsed",
                )
            with c2:
                if len(st.session_state.new_acts) > 1 and st.button("✕", key=f"rm_{i}"):
                    to_remove = i

        if to_remove is not None:
            st.session_state.new_acts.pop(to_remove)
            st.rerun()

        if st.button("＋ Add activity", key="np_add"):
            st.session_state.new_acts.append("")
            st.rerun()

        st.divider()
        if st.button("Create Profile", type="primary", key="np_create"):
            n    = name.strip()
            acts = [a.strip() for a in st.session_state.new_acts if a.strip()]
            if not n:
                st.error("Enter a profile name.")
            elif not acts:
                st.error("Add at least one activity.")
            elif os.path.exists(profile_path(n)):
                st.error(f'Profile "{n}" already exists.')
            else:
                create_profile(n, acts)
                st.success(f'✅ Profile "{n}" created with {len(acts)} activities!')
                st.session_state.new_acts = [""]
                st.session_state.current_profile = n
                st.rerun()


# ─── App shell ────────────────────────────────────────────────────────────────

profiles = list_profiles()

with st.sidebar:
    st.markdown("## 📅 Life Calendar")
    st.divider()

    if profiles:
        if (
            "current_profile" not in st.session_state
            or st.session_state.current_profile not in profiles
        ):
            st.session_state.current_profile = profiles[0]

        profile = st.selectbox(
            "👤 Profile", profiles,
            index=profiles.index(st.session_state.current_profile),
        )
        st.session_state.current_profile = profile
    else:
        profile = None
        st.caption("No profiles yet.")

    st.divider()

    page = st.radio(
        "",
        ["🏠 Dashboard", "📝 Add Entry", "🔍 Review", "📈 Charts", "🗂️ Arcs", "⚙️ Settings"],
        label_visibility="collapsed",
        key="nav_page",
    )

    st.divider()
    st.toggle("🌙 Dark mode", key="dark_mode")

page_key = page.split(" ", 1)[1]

if not profile and page_key != "Settings":
    st.title("📅 Life Calendar")
    st.info("👈 Go to **⚙️ Settings → New Profile** to get started.")
elif page_key == "Dashboard":
    st.title(f"📅 {profile.capitalize()}'s Calendar")
    page_dashboard(profile)
elif page_key == "Add Entry":
    st.title("📝 Add Entry")
    page_add_entry(profile)
elif page_key == "Review":
    st.title(f"🔍 Review — {profile.capitalize()}")
    page_review(profile)
elif page_key == "Charts":
    st.title(f"📈 Charts — {profile.capitalize()}")
    page_charts(profile)
elif page_key == "Arcs":
    st.title(f"🗂️ Arcs — {profile.capitalize()}")
    page_arcs(profile)
elif page_key == "Settings":
    title = f"⚙️ Settings — {profile.capitalize()}" if profile else "⚙️ Settings"
    st.title(title)
    page_settings(profile)
