# Laboratorio de Ciencia de Datos version 0.4.0

## Cambios de presentación
- Fondo general violeta mas profundo, en una tonalidad lavanda/plum suave.
- Barra lateral con violeta mass marcado.
- Paneles y tarjetas claros para conservar contraste y legibilidad.

## Funcionalidad
Esta actualización conserva las funciones verificadas de la versión 0.4.0:
- Carga, biblioteca y eliminación de archivos CSV.
- Consultas SQL con DuckDB.
- Perfil estadístico, limpieza, correlaciones y graficos.
- Exportación de resultados.

## Actualización en GitHub
1. Descomprime el ZIP.
2. Reemplaza `app.py` y `README.md` en el repositorio.
3. Conserva `requirements.txt` y la carpeta `data/`, incluidos tus CSV.
4. Haz Commit y espera el redeploy de Streamlit.

Esta versión modifica unicamente la presentación visual, el texto del crédito y las etiquetas de versiónn. No cambia la lógica de administración de archivos ni las consultas SQL.


## Versión 0.4.0  Inferencia estadística
Se incorpora un módulo de pruebas de hipótesis con t de Student (una muestra y pareadas), t de Welch (muestras independientes), ANOVA de un factor, chi-cuadrado de independencia, correlaciones de Pearson y Spearman, Shapiro-Wilk, Mann-Whitney U y Wilcoxon. Incluye nivel Î± configurable, hipótesis, estadístico, valor p, grados de libertad cuando aplican, decisión y advertencias metodológicas. Se retira el crédito de diseñoo de la interfaz.
