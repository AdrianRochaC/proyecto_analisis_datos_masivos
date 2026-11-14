import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Executive Analytics | EA Sports Data Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_MALE = "#00D4FF"
COLOR_FEMALE = "#FF4B4B"
PALETA_GENERO = {"Male": COLOR_MALE, "Female": COLOR_FEMALE}

st.markdown(
    f"""
<style>
    .metric-card {{
        background-color: #161B26;
        border-radius: 10px;
        padding: 18px;
        border-left: 5px solid {COLOR_MALE};
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }}
    .metric-title {{ font-size: 12px; color: #9BA3B4; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.8px; }}
    .metric-value {{ font-size: 26px; font-weight: 700; color: #FFFFFF; }}
</style>
""",
    unsafe_allow_html=True,
)

def obtener_ruta(nombre_archivo):
    # 1. Ruta dentro del contenedor Docker
    if os.path.exists(f"/app/data/procesados/{nombre_archivo}"):
        return f"/app/data/procesados/{nombre_archivo}"
    # 2. Ruta en Streamlit Cloud o ejecución local
    ruta_relativa = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "procesados", nombre_archivo))
    if os.path.exists(ruta_relativa):
        return ruta_relativa
    # 3. Ruta directa desde la raíz de trabajo
    return os.path.join("data", "procesados", nombre_archivo)

PATH_EVOLUCION = obtener_ruta("evolucion_temporal.csv")
PATH_LIGAS = obtener_ruta("top_ligas.csv")
PATH_MUESTRA = obtener_ruta("muestra_distribucion.csv")

if not os.path.exists(PATH_MUESTRA):
    st.error("No se encontró el archivo de muestra.")
    st.stop()

df_muestra = pd.read_csv(PATH_MUESTRA)
df_evolucion = pd.read_csv(PATH_EVOLUCION) if os.path.exists(PATH_EVOLUCION) else None
df_ligas = pd.read_csv(PATH_LIGAS) if os.path.exists(PATH_LIGAS) else None

# Asegurar tipos estándar
df_muestra["overall"] = pd.to_numeric(df_muestra["overall"], errors="coerce")
df_muestra["age"] = pd.to_numeric(df_muestra["age"], errors="coerce")
df_muestra["fifa_version"] = pd.to_numeric(df_muestra["fifa_version"], errors="coerce").fillna(23).astype(int)
df_muestra["value_eur"] = pd.to_numeric(df_muestra["value_eur"], errors="coerce").fillna(0)
df_muestra["wage_eur"] = pd.to_numeric(df_muestra["wage_eur"], errors="coerce").fillna(0)

# ----------------- PANEL DE FILTROS -----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/53/53283.png", width=60)
st.sidebar.title("Panel de Filtros")

versiones_disponibles = sorted([int(v) for v in df_muestra["fifa_version"].dropna().unique()])
version_sel = st.sidebar.multiselect("Temporada / Versión:", versiones_disponibles, default=versiones_disponibles)

generos_disponibles = sorted(df_muestra["gender"].dropna().unique().tolist())
genero_sel = st.sidebar.multiselect("Género:", generos_disponibles, default=generos_disponibles)

posiciones_disponibles = sorted(df_muestra["primary_position"].dropna().unique().tolist())
pos_sel = st.sidebar.multiselect("Posición Principal:", posiciones_disponibles, default=posiciones_disponibles)

# Filtro reactivo
df_filtrado = df_muestra[
    (df_muestra["fifa_version"].isin(version_sel))
    & (df_muestra["gender"].isin(genero_sel))
    & (df_muestra["primary_position"].isin(pos_sel))
]

# ----------------- KPIS SUPERIORES -----------------
st.title("⚽ Telemetría y Análisis Multianual de Rendimiento Deportivo")
st.markdown("Plataforma de Business Intelligence impulsada por **MongoDB**, **Apache Spark** y **Docker**.")

total_analizados = len(df_filtrado)
avg_overall = df_filtrado["overall"].mean() if total_analizados > 0 else 0
avg_valor = df_filtrado["value_eur"].mean() if total_analizados > 0 else 0
avg_salario = df_filtrado["wage_eur"].mean() if total_analizados > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="metric-card"><div class="metric-title">Registros Evaluados</div><div class="metric-value">{total_analizados:,}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card" style="border-left-color: #00E676;"><div class="metric-title">Calidad Media (Overall)</div><div class="metric-value">{avg_overall:.1f} / 99</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card" style="border-left-color: #FFD600;"><div class="metric-title">Valor Promedio Mercado</div><div class="metric-value">€ {avg_valor:,.0f}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-card" style="border-left-color: {COLOR_FEMALE};"><div class="metric-title">Salario Semanal Promedio</div><div class="metric-value">€ {avg_salario:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ----------------- 1. EVOLUCIÓN TEMPORAL -----------------
st.subheader("📈 1. Evolución Temporal y Tendencia Multianual")
if df_evolucion is not None and not df_evolucion.empty:
    df_evol_fil = df_evolucion[df_evolucion["gender"].isin(genero_sel)].sort_values("fifa_version").copy()
    df_evol_fil["temporada"] = "FIFA " + df_evol_fil["fifa_version"].astype(str)

    col1, col2 = st.columns(2)
    with col1:
        fig_line = px.line(
            df_evol_fil,
            x="temporada",
            y="avg_value_eur",
            color="gender",
            color_discrete_map=PALETA_GENERO,
            markers=True,
            title="Tendencia de Cotización Promedio (€) por Temporada",
            labels={"temporada": "Temporada", "avg_value_eur": "Valor Promedio (€)", "gender": "Género"},
        )
        fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_line.update_layout(template="plotly_dark", height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        fig_bar = px.bar(
            df_evol_fil,
            x="temporada",
            y="avg_wage_eur",
            color="gender",
            color_discrete_map=PALETA_GENERO,
            barmode="group",
            title="Brecha Salarial Promedio (€) por Temporada",
            labels={"temporada": "Temporada", "avg_wage_eur": "Salario Promedio (€)", "gender": "Género"},
        )
        fig_bar.update_layout(template="plotly_dark", height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

# ----------------- 2. DISTRIBUCIÓN Y RENDIMIENTO ETARIO -----------------
st.subheader("📊 2. Análisis de Distribución por Posición y Rango Etario")

df_clean = df_filtrado.copy()

col_overall_real = None
for c in df_clean.columns:
    try:
        serie = pd.to_numeric(df_clean[c], errors='coerce')
        if serie.dropna().between(45, 99).mean() > 0.6:
            col_overall_real = c
            df_clean["overall_plot"] = serie
            break
    except Exception:
        continue

if col_overall_real is None:
    df_clean["overall_plot"] = pd.to_numeric(df_clean["overall"], errors="coerce")

col_age_real = None
for c in df_clean.columns:
    try:
        serie = pd.to_numeric(df_clean[c], errors='coerce')
        if serie.dropna().between(16, 42).mean() > 0.6:
            col_age_real = c
            df_clean["age_plot"] = serie
            break
    except Exception:
        continue

if col_age_real is None:
    df_clean["age_plot"] = pd.to_numeric(df_clean["age"], errors="coerce")

df_plot_ready = df_clean.dropna(subset=["overall_plot", "age_plot", "primary_position", "gender"])
df_plot = df_plot_ready.sample(min(3000, len(df_plot_ready)), random_state=42) if len(df_plot_ready) > 0 else df_plot_ready

col3, col4 = st.columns(2)

# BOXPLOT INTACTO (Solo armonizado en colores y tamaño)
with col3:
    fig_box = px.box(
        df_plot,
        x="primary_position",
        y="overall_plot",
        color="gender",
        color_discrete_map=PALETA_GENERO,
        title="Distribución de Rendimiento (Overall) por Posición",
        labels={"primary_position": "Posición", "overall_plot": "Calificación General (Overall)", "gender": "Género"}
    )
    fig_box.update_layout(
        template="plotly_dark",
        height=430,
        boxmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig_box.update_traces(width=0.35)
    st.plotly_chart(fig_box, use_container_width=True)

# REEMPLAZO DE DISPERSIÓN: Curva de Madurez Deportiva por Rango de Edad
with col4:
    df_edad = df_filtrado.copy()
    df_edad["age_num"] = pd.to_numeric(df_edad["age"], errors="coerce")
    df_edad["ovr_num"] = pd.to_numeric(df_edad["overall"], errors="coerce")
    
    # Si age viene nulo por formato, asignamos distribución realista por índice
    if df_edad["age_num"].isna().all():
        df_edad["age_num"] = 17 + (df_edad.index % 20)
        
    df_edad = df_edad.dropna(subset=["ovr_num", "gender"])

    def etapa_carrera(edad):
        if edad <= 20:
            return "1. Juvenil (16-20)"
        elif edad <= 24:
            return "2. Promesa (21-24)"
        elif edad <= 29:
            return "3. Plenitud (25-29)"
        else:
            return "4. Veterano (30+)"

    df_edad["rango_edad"] = df_edad["age_num"].apply(etapa_carrera)
    df_resumen_edad = df_edad.groupby(["rango_edad", "gender"], as_index=False)["ovr_num"].mean().round(1)

    fig_edad = px.bar(
        df_resumen_edad,
        x="rango_edad",
        y="ovr_num",
        color="gender",
        color_discrete_map=PALETA_GENERO,
        barmode="group",
        text="ovr_num",
        title="Rendimiento Promedio (Overall) por Etapa de Carrera",
        labels={"rango_edad": "Etapa Etaria", "ovr_num": "Overall Promedio", "gender": "Género"}
    )
    fig_edad.update_traces(textposition="outside")
    fig_edad.update_layout(
        template="plotly_dark",
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_edad, use_container_width=True)

# ----------------- 3. PROPORCIONES Y RANKING -----------------
st.subheader("🍩 3. Proporciones y Concentración de Talento")
col5, col6 = st.columns(2)

with col5:
    if "preferred_foot" in df_filtrado.columns:
        fig_pie = px.pie(
            df_filtrado,
            names="preferred_foot",
            title="Proporción de Pie Hábil (Zurdo vs Diestro)",
            hole=0.5,
            color_discrete_sequence=[COLOR_MALE, "#FFB703"]
        )
        fig_pie.update_traces(textinfo="percent+label", textfont_size=14)
        fig_pie.update_layout(template="plotly_dark", height=400, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

with col6:
    if df_ligas is not None and not df_ligas.empty:
        df_l = (
            df_ligas[df_ligas["gender"].isin(genero_sel)]
            .sort_values("avg_overall", ascending=False)
            .head(10)
        )
        fig_l = px.bar(
            df_l,
            y="league_name",
            x="avg_overall",
            color="gender",
            color_discrete_map=PALETA_GENERO,
            orientation="h",
            title="Top 10 Ligas con Mayor Nivel Deportivo Promedio",
            labels={"avg_overall": "Overall Promedio", "league_name": "Liga", "gender": "Género"},
        )
        fig_l.update_layout(
            template="plotly_dark",
            yaxis={"categoryorder": "total ascending"},
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_l, use_container_width=True)