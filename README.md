# Laboratorio de Ciencia de Datos â€” versiÃ³n 0.4.0

## Cambios de presentaciÃ³n
- Fondo general violeta mÃ¡s profundo, en una tonalidad lavanda/plum suave.
- Barra lateral con violeta mÃ¡s marcado.
- Paneles y tarjetas claros para conservar contraste y legibilidad.

## Funcionalidad
Esta actualizaciÃ³n conserva las funciones verificadas de la versiÃ³n 0.4.0:
- Carga, biblioteca y eliminaciÃ³n de archivos CSV.
- Consultas SQL con DuckDB.
- Perfil estadÃ­stico, limpieza, correlaciones y grÃ¡ficos.
- ExportaciÃ³n de resultados.

## ActualizaciÃ³n en GitHub
1. Descomprime el ZIP.
2. Reemplaza `app.py` y `README.md` en el repositorio.
3. Conserva `requirements.txt` y la carpeta `data/`, incluidos tus CSV.
4. Haz Commit y espera el redeploy de Streamlit.

Esta versiÃ³n modifica Ãºnicamente la presentaciÃ³n visual, el texto del crÃ©dito y las etiquetas de versiÃ³n. No cambia la lÃ³gica de administraciÃ³n de archivos ni las consultas SQL.


## VersiÃ³n 0.4.0 â€” Inferencia estadÃ­stica
Se incorpora un mÃ³dulo de pruebas de hipÃ³tesis con t de Student (una muestra y pareadas), t de Welch (muestras independientes), ANOVA de un factor, chi-cuadrado de independencia, correlaciones de Pearson y Spearman, Shapiro-Wilk, Mann-Whitney U y Wilcoxon. Incluye nivel Î± configurable, hipÃ³tesis, estadÃ­stico, valor p, grados de libertad cuando aplican, decisiÃ³n y advertencias metodolÃ³gicas. Se retira el crÃ©dito de diseÃ±o de la interfaz.
