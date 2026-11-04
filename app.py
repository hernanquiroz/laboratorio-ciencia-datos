import io
import json
from datetime import datetime

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Laboratorio de Ciencia de Datos",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Laboratorio de Ciencia de Datos")
st.caption("Prototipo 0.1 · Python + DuckDB + Parquet + Streamlit")
st.markdown(
    "Carga un archivo, explora su estructura, ejecuta consultas SQL y "
    "genera visualizaciones. Los datos se procesan durante la sesión."
)

if "duckdb_connection" not in st.session_state:
    st.session_state["duckdb_connection"] = duckdb.connect(database=":memory:")

con = st.session_state["duckdb_connection"]

with st.sidebar:
    st.header("1. Fuente de datos")
    uploaded = st.file_uploader(
        "Carga un archivo CSV o Parquet",
        type=["csv", "parquet"],
        help="Para este prototipo se admiten archivos CSV y Parquet.",
    )
    use_sample = st.checkbox("Usar conjunto de datos de ejemplo", value=uploaded is None)
    st.divider()
    st.header("2. Tabla activa")
    st.caption("La tabla cargada se registra como `datos`.")

def register_data(file, sample):
    if file is not None:
        raw = file.getvalue()
        suffix = file.name.lower().rsplit(".", 1)[-1]
        if suffix == "csv":
            con.register("_uploaded_bytes", pd.read_csv(io.BytesIO(raw)))
            con.execute("CREATE OR REPLACE TABLE datos AS SELECT * FROM _uploaded_bytes")
            con.unregister("_uploaded_bytes")
        else:
            # DuckDB lee el Parquet desde un archivo temporal de la sesión.
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                tmp.write(raw)
                tmp_path = tmp.name
            con.execute(
                "CREATE OR REPLACE TABLE datos AS "
                "SELECT * FROM read_parquet(?)",
                [tmp_path],
            )
        return file.name
    if sample:
        sample_df = pd.DataFrame({
            "fecha": pd.date_range("2025-01-01", periods=24, freq="MS"),
            "municipio": ["Medellín", "Bello", "Itagüí", "Envigado"] * 6,
            "temperatura_c": [22.1, 21.8, 23.0, 22.5, 22.8, 22.0, 23.4, 22.9,
                              23.1, 22.6, 23.7, 23.2, 22.4, 21.9, 23.3, 22.7,
                              23.8, 23.0, 24.1, 23.5, 22.9, 22.2, 23.6, 23.1],
            "humedad_pct": [78, 80, 74, 76, 77, 82, 72, 75, 73, 79, 70, 74,
                            81, 83, 75, 78, 71, 73, 68, 72, 79, 81, 74, 76],
            "precipitacion_mm": [120, 135, 110, 115, 140, 155, 95, 105, 90, 130,
                                 80, 100, 160, 170, 125, 145, 75, 85, 65, 90,
                                 150, 165, 115, 130],
        })
        con.register("_sample_df", sample_df)
        con.execute("CREATE OR REPLACE TABLE datos AS SELECT * FROM _sample_df")
        con.unregister("_sample_df")
        return "Datos de ejemplo"
    return None

source_name = register_data(uploaded, use_sample)

if not source_name:
    st.info("Carga un archivo CSV/Parquet o activa el conjunto de datos de ejemplo en la barra lateral.")
    st.stop()

st.success(f"Fuente activa: {source_name}")

# Overview
row = con.execute("SELECT COUNT(*) FROM datos").fetchone()
columns = con.execute("DESCRIBE datos").df()
column_names = columns["column_name"].tolist()
preview = con.execute("SELECT * FROM datos LIMIT 1000").df()

c1, c2, c3 = st.columns(3)
c1.metric("Registros", f"{row[0]:,}")
c2.metric("Variables", len(column_names))
c3.metric("Columnas numéricas", int(preview.select_dtypes(include="number").shape[1]))

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Exploración", "🧮 SQL con DuckDB", "📊 Visualización", "⬇️ Exportar"]
)

with tab1:
    st.subheader("Vista previa")
    st.dataframe(preview, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Esquema")
        st.dataframe(columns, use_container_width=True)
    with right:
        st.subheader("Estadística descriptiva")
        st.dataframe(preview.describe(include="all").transpose(), use_container_width=True)
    missing_rows = []
    for col in column_names:
        safe_col = col.replace('"', '""')
        count = con.execute(f'SELECT COUNT(*) FROM datos WHERE "{safe_col}" IS NULL').fetchone()[0]
        missing_rows.append({"variable": col, "valores_nulos": count,
                             "porcentaje_nulos": round(count / max(row[0], 1) * 100, 2)})
    st.subheader("Calidad básica: valores nulos")
    st.dataframe(pd.DataFrame(missing_rows), use_container_width=True)

with tab2:
    st.subheader("Consultas SQL")
    st.markdown("Consulta la tabla **`datos`**. Ejemplo: `SELECT * FROM datos LIMIT 20`.")
    default_sql = "SELECT * FROM datos LIMIT 20"
    sql = st.text_area("Consulta SQL", value=default_sql, height=130)
    if st.button("▶ Ejecutar consulta", type="primary"):
        try:
            result = con.execute(sql).df()
            st.session_state["sql_result"] = result
            st.session_state["sql_text"] = sql
            st.success(f"Consulta ejecutada: {len(result):,} filas devueltas.")
        except Exception as exc:
            st.error(f"No se pudo ejecutar la consulta: {exc}")
    if "sql_result" in st.session_state:
        st.dataframe(st.session_state["sql_result"], use_container_width=True)
        st.download_button(
            "Descargar resultado CSV",
            data=st.session_state["sql_result"].to_csv(index=False).encode("utf-8-sig"),
            file_name="resultado_consulta.csv",
            mime="text/csv",
        )

with tab3:
    st.subheader("Gráfico exploratorio")
    numeric_cols = preview.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.warning("No se detectaron columnas numéricas para graficar.")
    else:
        x_options = ["(índice)"] + column_names
        x_col = st.selectbox("Variable para eje X", x_options, index=0)
        y_col = st.selectbox("Variable numérica para eje Y", numeric_cols)
        color_options = ["(ninguna)"] + column_names
        color_col = st.selectbox("Agrupar por color (opcional)", color_options)
        plot_df = preview.copy()
        if x_col == "(índice)":
            plot_df["_fila"] = range(1, len(plot_df) + 1)
            x_actual = "_fila"
        else:
            x_actual = x_col
        color_actual = None if color_col == "(ninguna)" else color_col
        fig = px.scatter(
            plot_df, x=x_actual, y=y_col, color=color_actual,
            title=f"{y_col} según {x_actual}",
            trendline=None,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Gráfico exploratorio sobre la vista previa (máximo 1.000 filas).")

with tab4:
    st.subheader("Exportación")
    csv_bytes = preview.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar vista previa como CSV",
        data=csv_bytes,
        file_name="datos_explorados.csv",
        mime="text/csv",
    )
    parquet_buffer = io.BytesIO()
    preview.to_parquet(parquet_buffer, index=False)
    st.download_button(
        "Descargar vista previa como Parquet",
        data=parquet_buffer.getvalue(),
        file_name="datos_explorados.parquet",
        mime="application/octet-stream",
    )
    report = {
        "prototipo": "Laboratorio de Ciencia de Datos 0.1",
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "fuente": source_name,
        "registros": int(row[0]),
        "variables": column_names,
        "esquema": columns.to_dict(orient="records"),
    }
    st.download_button(
        "Descargar resumen técnico JSON",
        data=json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="resumen_tecnico.json",
        mime="application/json",
    )

st.divider()
st.caption(
    "Prototipo educativo y experimental. No reemplaza validaciones estadísticas, "
    "controles de calidad exhaustivos ni auditorías de seguridad para producción."
)
