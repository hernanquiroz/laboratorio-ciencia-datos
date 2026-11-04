# Laboratorio de Ciencia de Datos — Prototipo 0.1

Aplicación inicial con Streamlit + DuckDB para explorar archivos CSV/Parquet,
consultar datos mediante SQL, revisar esquema y valores nulos, visualizar
variables numéricas y exportar resultados.

## Ejecutar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Desplegar en Streamlit Community Cloud

1. Crea un repositorio GitHub, por ejemplo `laboratorio-ciencia-datos`.
2. Sube `app.py` y `requirements.txt`.
3. En Streamlit Community Cloud selecciona el repositorio y `app.py`.
4. Despliega la aplicación.

## Uso

- Carga CSV o Parquet desde la barra lateral.
- O utiliza los datos climáticos sintéticos de ejemplo.
- Explora esquema, vista previa y valores nulos.
- Ejecuta consultas SQL sobre la tabla `datos`.
- Crea gráficos exploratorios.
- Descarga resultados CSV, Parquet y un resumen JSON.

## Alcance y límites del prototipo

- Los datos se cargan en una conexión DuckDB en memoria durante la sesión.
- La vista previa y los gráficos están limitados a 1.000 filas para mantener
  la interfaz ágil; las consultas SQL operan sobre la tabla completa.
- La aplicación no conserva los archivos entre sesiones.
- No incluye todavía autenticación, persistencia, trabajos en segundo plano,
  modelos predictivos ni agentes de IA.
- Antes de usar datos sensibles, implementar controles de acceso y privacidad.

## Próxima evolución sugerida

0.2: perfilado avanzado, detección de tipos, filtros, exportación de consultas,
validación con Pandera y almacenamiento Parquet.
0.3: análisis estadístico, correlaciones, pruebas de hipótesis y modelos
Scikit-learn con evaluación y trazabilidad.
0.4: MLflow, visualización geoespacial y agentes de IA con ejecución controlada.
