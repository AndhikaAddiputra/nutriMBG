from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import streamlit as st
import requests
import datetime

# ... (Existing imports and setup)

st.header("Laporan Gizi Mingguan")

col1, col2 = st.columns([2, 1])

with col1:
    # Set default to the monday of the current week
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    selected_week_start = st.date_input("Tanggal Mulai Minggu (Senin)", value=monday)
    sppg_name = st.text_input("Nama SPPG", value="SPPG Jakarta")

with col2:
    st.write("") # Spacing
    st.write("")
    
    # We load the PDF from the backend endpoint
    if st.button("Generate Laporan"):
        with st.spinner("Memproses PDF dalam <10 detik..."):
            backend_url = f"http://localhost:8000/reports/weekly" # adjust port/url based on docker-compose
            params = {
                "week_start": selected_week_start.strftime("%Y-%m-%d"),
                "sppg_name": sppg_name
            }
            
            try:
                response = requests.get(backend_url, params=params)
                if response.status_code == 200:
                    filename = f"laporan_mingguan_{sppg_name.replace(' ', '_')}_{selected_week_start}.pdf"
                    st.success("Laporan berhasil dibuat!")
                    
                    # Display the Streamlit native download button
                    st.download_button(
                        label="Unduh Laporan Mingguan (PDF)",
                        data=response.content,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error(f"Gagal mengambil laporan dari server. (Code: {response.status_code})")
            except requests.exceptions.RequestException as e:
                st.error("Koneksi ke backend gagal.")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

COMPONENT_LABELS: Dict[str, str] = {
    "composite":    "Skor Komposit",
    "protein":      "Protein",
    "carbohydrate": "Karbohidrat",
    "fat":          "Lemak",
    "fiber":        "Serat",
    "iron":         "Zat Besi",
    "vitamin_a":    "Vitamin A",
}

EDUCATION_LEVELS = {
    "SD Kelas 1–3": "SD_1_3",
    "SD Kelas 4–6": "SD_4_6",
    "SMP":          "SMP",
    "SMA":          "SMA",
}

# Color palette — one distinct color per component
COMPONENT_COLORS: Dict[str, str] = {
    "composite":    "#4C72B0",
    "protein":      "#DD8452",
    "carbohydrate": "#55A868",
    "fat":          "#C44E52",
    "fiber":        "#8172B2",
    "iron":         "#937860",
    "vitamin_a":    "#DA8BC3",
}

# ---------------------------------------------------------------------------
# Data fetching (cached)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner=False)
def fetch_trend(
    days: int,
    component: str,
    education_level: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Call GET /api/v1/history/trend and return the raw JSON list,
    or None on any network / server error.
    """
    try:
        resp = requests.get(
            f"{API_BASE_URL}/api/v1/history/trend",
            params={
                "days": days,
                "component": component,
                "education_level": education_level,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"⚠️ Gagal memuat data tren dari backend: {exc}")
        return None


# ---------------------------------------------------------------------------
# Chart rendering
# ---------------------------------------------------------------------------


def _render_chart(series_data: List[Dict[str, Any]], selected_labels: List[str]) -> None:
    """
    Build and render a Plotly figure from the list of TrendResponse objects.

    Parameters
    ----------
    series_data     : list of TrendResponse dicts from the API
    selected_labels : human-readable component names chosen by the user
    """
    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        st.error("Paket `plotly` tidak terinstal. Tambahkan ke requirements.txt.")
        return

    # Invert label map so we can look up component key by label
    label_to_key = {v: k for k, v in COMPONENT_LABELS.items()}
    selected_keys = {label_to_key[lbl] for lbl in selected_labels}

    fig = go.Figure()

    any_flagged_global = False

    for series in series_data:
        comp = series["component"]
        if comp not in selected_keys:
            continue

        data_pts = series["data"]
        if not data_pts:
            continue

        dates  = [pt["date"]  for pt in data_pts]
        scores = [pt["score"] for pt in data_pts]
        flags  = [pt["is_flagged"] for pt in data_pts]

        color = COMPONENT_COLORS.get(comp, "#888888")
        label = COMPONENT_LABELS.get(comp, comp)

        # ── Main line trace ──────────────────────────────────────────────
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=scores,
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=5, color=color),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{label}: %{{y:.1f}}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # ── Outlier scatter (red dot on top) ────────────────────────────
        flagged_dates  = [d for d, f in zip(dates, flags)  if f]
        flagged_scores = [s for s, f in zip(scores, flags) if f]

        if flagged_dates:
            any_flagged_global = True
            fig.add_trace(
                go.Scatter(
                    x=flagged_dates,
                    y=flagged_scores,
                    mode="markers",
                    name=f"{label} ⚠ Di Bawah Rata-rata",
                    marker=dict(
                        symbol="circle",
                        size=12,
                        color="red",
                        line=dict(color="darkred", width=1.5),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"⚠ {label} rendah: %{{y:.1f}}<br>"
                        "<extra></extra>"
                    ),
                )
            )

    # ── Layout ──────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text="Tren Skor Gizi Harian (28 Hari Terakhir)",
            font=dict(size=16),
        ),
        xaxis=dict(
            title="Tanggal",
            tickformat="%d %b",
            showgrid=True,
            gridcolor="#EEEEEE",
        ),
        yaxis=dict(
            title="Skor (%)",
            range=[0, 105],
            showgrid=True,
            gridcolor="#EEEEEE",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=60, b=40),
        height=480,
    )

    st.plotly_chart(fig, use_container_width=True)

    if any_flagged_global:
        st.caption(
            "🔴 Titik merah menunjukkan tanggal dengan skor > 1 standar deviasi "
            "di bawah rata-rata — indikasi potensi masalah kualitas menu."
        )


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Riwayat Gizi – NutriMBG", layout="wide")

st.title("📈 Pelacak Tren Gizi Mingguan")
st.write(
    "Pantau tren skor gizi harian selama 4 minggu terakhir. "
    "Titik merah menandai tanggal dengan skor di bawah rata-rata secara signifikan."
)

# ── Sidebar / control strip ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Filter")

    jenjang_label = st.selectbox(
        "Jenjang Pendidikan (AKG)",
        list(EDUCATION_LEVELS.keys()),
        index=2,  # default: SMP
    )
    education_level_code = EDUCATION_LEVELS[jenjang_label]

    rolling_days = st.selectbox(
        "Rentang Waktu",
        options=[7, 14, 21, 28],
        index=3,
        format_func=lambda d: f"{d} hari terakhir",
    )

    all_component_labels = list(COMPONENT_LABELS.values())
    selected_labels = st.multiselect(
        "Komponen Gizi",
        options=all_component_labels,
        default=["Skor Komposit"],
        help="Pilih satu atau lebih komponen untuk ditampilkan di grafik.",
    )

    refresh = st.button("🔄 Perbarui Data", use_container_width=True)

# ── Main area ───────────────────────────────────────────────────────────────

if not selected_labels:
    st.info("Pilih minimal satu komponen gizi di panel kiri untuk menampilkan grafik.")
    st.stop()

# Derive the API component param: if all components selected → "all"
label_to_key = {v: k for k, v in COMPONENT_LABELS.items()}
selected_keys = [label_to_key[lbl] for lbl in selected_labels]

if set(selected_keys) == set(COMPONENT_LABELS.keys()):
    api_component = "all"
else:
    # Fetch all and let the chart filter client-side — simpler than N calls
    api_component = "all"

if refresh:
    st.cache_data.clear()

with st.spinner("Memuat data tren…"):
    raw_series = fetch_trend(
        days=rolling_days,
        component=api_component,
        education_level=education_level_code,
    )

if raw_series is None:
    st.stop()

# ── Empty-state guard ───────────────────────────────────────────────────────
# Aggregate data points across all series to count distinct days
all_dates = set()
for series in raw_series:
    for pt in series.get("data", []):
        all_dates.add(pt["date"])

if len(all_dates) < 7:
    st.info(
        "📭 Butuh minimal 7 hari data untuk menampilkan grafik tren. "
        f"Saat ini tersedia data untuk {len(all_dates)} hari. "
        "Lakukan lebih banyak analisis menu agar tren dapat ditampilkan."
    )
    st.stop()

# ── Render chart ─────────────────────────────────────────────────────────────
_render_chart(raw_series, selected_labels)

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader("Ringkasan per Komponen")

summary_rows = []
for series in raw_series:
    comp = series["component"]
    label = COMPONENT_LABELS.get(comp, comp)
    if label not in selected_labels:
        continue
    pts = series.get("data", [])
    if not pts:
        summary_rows.append(
            {"Komponen": label, "Hari Data": 0, "Rata-rata": "–", "Hari Merah": 0}
        )
        continue
    scores = [pt["score"] for pt in pts]
    flagged = sum(1 for pt in pts if pt["is_flagged"])
    summary_rows.append(
        {
            "Komponen": label,
            "Hari Data": len(pts),
            "Rata-rata": f"{sum(scores)/len(scores):.1f}%",
            "Hari Bermasalah 🔴": flagged,
        }
    )

if summary_rows:
    st.table(summary_rows)

st.caption(
    f"Data diambil dari endpoint `/api/v1/history/trend` · "
    f"Cache diperbarui setiap 5 menit · "
    f"Jenjang AKG: **{jenjang_label}**"
)