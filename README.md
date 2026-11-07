[README.md](https://github.com/user-attachments/files/34525342/README.md)
# Laboratorio de Ciencia de Datos — versión 0.3.1

## Correcciones y novedades
- SQL: valida que se ejecute una sola sentencia por vez; incluye ejemplos seleccionables para evitar el error del parser al pegar varios SELECT juntos.
- Incluye pestaña de ciclo de vida y limpieza: diagnóstico, espacios, cadenas vacías, duplicados, valores faltantes, detección/recorte IQR y bitácora.
- Conserva el CSV original y aplica acciones a una copia de trabajo; permite restaurarla.
- Incluye un CSV sintético didáctico de cambio climático (no son mediciones reales ni el archivo original del usuario).
- Perfil estadístico, correlaciones, gráficos, DuckDB y exportación CSV/Parquet/JSON.

## Instalación local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub / Streamlit
1. Descomprime el ZIP.
2. Reemplaza `app.py` y `requirements.txt` en el repositorio.
3. Sube también `README.md` y el contenido de `data/`.
4. Haz commit y espera el despliegue.

## Archivo de cambio climático
`data/ejemplo_cambio_climatico_sintetico.csv` es un conjunto generado para probar la aplicación. No sustituye el CSV original que el usuario había cargado. Ese archivo original no apareció entre los archivos disponibles en esta conversación/biblioteca; debe volver a cargarse para integrarlo como fuente real.

## Persistencia
Los CSV de `data/csv_guardados/` se guardan en el disco local de la instancia. Streamlit Community Cloud no garantiza persistencia tras reinicios o redeploys. Para almacenamiento duradero se requiere conectar almacenamiento externo y guardar credenciales en Secrets. No publiques datos personales en un repositorio público.
