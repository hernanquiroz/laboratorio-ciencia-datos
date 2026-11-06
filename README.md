# Laboratorio de Ciencia de Datos — Prototipo 0.2

## Correcciones
- Una conexión DuckDB nueva por ejecución de Streamlit.
- Eliminación de la conexión compartida mediante `st.cache_resource`.
- Consumo inmediato de resultados DuckDB con `fetchdf`, `fetchone` y `fetchall`.
- Prioridad automática al CSV/Parquet cargado; el conjunto de ejemplo se desactiva.
- Detección automática de separador CSV y lectura de codificaciones UTF-8, CP1252 y Latin-1.
- Se conservan exploración, SQL, gráficos y exportaciones.

## Despliegue en Streamlit Community Cloud
1. Descomprime el ZIP.
2. En GitHub, abre el repositorio `laboratorio-ciencia-datos`.
3. Reemplaza `app.py` y `requirements.txt` por los de esta versión.
4. Sube también README.md, .gitignore y la carpeta data si lo deseas.
5. Mantén `app.py` como archivo principal y espera el redeploy.

## Ejecución local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Límites
DuckDB trabaja en memoria durante la sesión. La vista previa y los gráficos muestran
hasta 1.000 filas; las consultas SQL trabajan sobre la tabla completa. Todavía no
hay persistencia ni autenticación.
