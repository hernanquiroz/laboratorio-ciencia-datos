import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Laboratorio de Ciencia de Datos", page_icon="🔬", layout="wide")
st.title("🔬 Laboratorio de Ciencia de Datos")
st.caption("Prototipo 0.2 · Python + DuckDB + Parquet + Streamlit")
st.write("Carga un archivo, explora su estructura, ejecuta consultas SQL y genera visualizaciones.")

# Una conexión independiente por ejecución evita conflictos de resultados
# pendientes al reutilizar conexiones DuckDB entre reruns de Streamlit.
con = duckdb.connect(database=":memory:")


def read_csv_robust(raw: bytes) -> pd.DataFrame:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=encoding)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"No se pudo interpretar el CSV: {last_error}")


def register_dataframe(frame: pd.DataFrame) -> None:
    con.register("_source_dataframe", frame)
    try:
        con.execute("CREATE OR REPLACE TABLE datos AS SELECT * FROM _source_dataframe").fetchall()
    finally:
        con.unregister("_source_dataframe")


with st.sidebar:
    st.header("1. Fuente de datos")
    uploaded = st.file_uploader("Carga un archivo CSV o Parquet", type=["csv", "parquet"])
    if uploaded is None:
        use_sample = st.checkbox("Usar conjunto de datos de ejemplo", value=True)
    else:
        use_sample = False
        st.caption("Se utilizará el archivo que acabas de cargar.")
    st.divider()
    st.header("2. Tabla activa")
    st.caption("La tabla cargada se registra como `datos`.")

source_name = None
try:
    if uploaded is not None:
        raw = uploaded.getvalue()
        extension = Path(uploaded.name).suffix.lower()
        if extension == ".csv":
            frame = read_csv_robust(raw)
            if len(frame.columns) == 0:
                raise ValueError("El CSV no contiene columnas reconocibles.")
            register_dataframe(frame)
        elif extension == ".parquet":
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                tmp.write(raw)
                parquet_path = tmp.name
            try:
                con.execute(
                    "CREATE OR REPLACE TABLE datos AS SELECT * FROM read_parquet(?)",
                    [parquet_path],
                ).fetchall()
            finally:
                Path(parquet_path).unlink(missing_ok=True)
        else:
            raise ValueError("Formato no admitido. Utiliza CSV o Parquet.")
        source_name = uploaded.name
    elif use_sample:
        sample = pd.DataFrame({
            "fecha": pd.date_range("2025-01-01", periods=24, freq="MS"),
            "municipio": ["Medellín", "Bello", "Itagüí", "Envigado"] * 6,
            "temperatura_c": [22.1,21.8,23.0,22.5,22.8,22.0,23.4,22.9,23.1,22.6,23.7,23.2,22.4,21.9,23.3,22.7,23.8,23.0,24.1,23.5,22.9,22.2,23.6,23.1],
            "humedad_pct": [78,80,74,76,77,82,72,75,73,79,70,74,81,83,75,78,71,73,68,72,79,81,74,76],
            "precipitacion_mm": [120,135,110,115,140,155,95,105,90,130,80,100,160,170,125,145,75,85,65,90,150,165,115,130],
        })
        register_dataframe(sample)
        source_name = "Datos de ejemplo"
    else:
        st.info("Carga un archivo CSV/Parquet o activa el conjunto de datos de ejemplo.")
        st.stop()
except Exception as exc:
    st.error(f"No se pudo cargar la fuente de datos: {exc}")
    st.info("Comprueba que el archivo sea un CSV o Parquet válido.")
    st.stop()

st.success(f"Fuente activa: {source_name}")

# Consumir cada resultado de DuckDB inmediatamente.
total_rows = con.execute("SELECT COUNT(*) FROM datos").fetchone()[0]
schema = con.execute("DESCRIBE datos").fetchdf()
column_names = schema["column_name"].tolist()
preview = con.execute("SELECT * FROM datos LIMIT 1000").fetchdf()
numeric_columns = preview.select_dtypes(include="number").columns.tolist()

a, b, c = st.columns(3)
a.metric("Registros", f"{total_rows:,}")
b.metric("Variables", len(column_names))
c.metric("Variables numéricas", len(numeric_columns))

tab1, tab2, tab3, tab4 = st.tabs(["📋 Exploración", "🧮 SQL con DuckDB", "📊 Visualización", "⬇️ Exportar"])

with tab1:
    st.subheader("Vista previa")
    st.dataframe(preview, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.subheader("Esquema de datos")
        st.dataframe(schema, use_container_width=True)
    with right:
        st.subheader("Estadística descriptiva")
        st.dataframe(preview.describe(include="all").transpose(), use_container_width=True)

    missing = []
    for col in column_names:
        safe = col.replace('"', '""')
        count = con.execute(f'SELECT COUNT(*) FROM datos WHERE "{safe}" IS NULL').fetchone()[0]
        missing.append({
            "variable": col,
            "valores_nulos": count,
            "porcentaje_nulos": round(count / max(total_rows, 1) * 100, 2),
        })
    st.subheader("Calidad básica: valores nulos")
    st.dataframe(pd.DataFrame(missing), use_container_width=True)

with tab2:
    st.subheader("Consultas SQL")
    st.caption("Consulta la tabla `datos`. Ejemplo: SELECT * FROM datos LIMIT 20")
    sql = st.text_area("Consulta SQL", "SELECT * FROM datos LIMIT 20", height=130, key="sql_query")
    if st.button("▶ Ejecutar consulta", type="primary"):
        try:
            result = con.execute(sql).fetchdf()
            st.session_state["sql_result"] = result
            st.success(f"Consulta ejecutada: {len(result):,} filas devueltas.")
        except Exception as exc:
            st.error(f"No se pudo ejecutar la consulta: {exc}")
    if "sql_result" in st.session_state:
        st.dataframe(st.session_state["sql_result"], use_container_width=True)
        st.download_button(
            "Descargar resultado CSV",
            st.session_state["sql_result"].to_csv(index=False).encode("utf-8-sig"),
            "resultado_consulta.csv",
            "text/csv",
        )

with tab3:
    st.subheader("Gráfico exploratorio")
    if not numeric_columns:
        st.warning("No se detectaron columnas numéricas.")
    else:
        x_col = st.selectbox("Variable para eje X", ["(índice)"] + column_names)
        y_col = st.selectbox("Variable numérica para eje Y", numeric_columns)
        color_col = st.selectbox("Agrupar por color (opcional)", ["(ninguna)"] + column_names)
        plot_df = preview.copy()
        if x_col == "(índice)":
            plot_df["_fila"] = range(1, len(plot_df) + 1)
            x_actual = "_fila"
        else:
            x_actual = x_col
        color_actual = None if color_col == "(ninguna)" else color_col
        fig = px.scatter(plot_df, x=x_actual, y=y_col, color=color_actual, title=f"{y_col} según {x_actual}")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Gráfico sobre la vista previa (máximo 1.000 filas).")

with tab4:
    st.subheader("Exportación")
    st.download_button(
        "Descargar vista previa como CSV",
        preview.to_csv(index=False).encode("utf-8-sig"),
        "datos_explorados.csv",
        "text/csv",
    )
    parquet_buffer = io.BytesIO()
    preview.to_parquet(parquet_buffer, index=False)
    st.download_button(
        "Descargar vista previa como Parquet",
        parquet_buffer.getvalue(),
        "datos_explorados.parquet",
        "application/octet-stream",
    )
    report = {
        "prototipo": "Laboratorio de Ciencia de Datos 0.2",
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "fuente": source_name,
        "registros": int(total_rows),
        "variables": column_names,
        "esquema": schema.to_dict(orient="records"),
    }
    st.download_button(
        "Descargar resumen técnico JSON",
        json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
        "resumen_tecnico.json",
        "application/json",
    )

st.divider()
st.caption("Prototipo experimental. DuckDB trabaja en memoria durante la sesión; los archivos no se conservan entre sesiones.")
