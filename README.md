# Laboratorio de Ciencia de Datos ” versión 0.4.1

## Corrección principal
- El módulo de inferencia recibe expli­citamente el mismo DataFrame `clean` que alimenta los demass módulos. Ya no busca claves de sesión (`df`, `datos_df`, etc.) que no existian, causa del mensaje â€œCarga un archivo CSV y activa sus datosâ€.
- Se muestra una confirmaciÃ³n de conexiÃ³n con el nÃºmero de filas y variables.

## Inferencia estadÃ­stica
Se conservan las diez pruebas: t de Student para una muestra, t de Welch para muestras independientes, t de Student pareada, ANOVA, chi-cuadrado, Pearson, Spearman, Shapiro-Wilk, Mann-Whitney U y Wilcoxon.

## Validación de instrumentos
- Alfa de Cronbach con selecciónn de i­tems, recodificación de i­tems inversos, interpretación orientativa, correlación i­tem-total corregida y alfa al eliminar cada i­tem.
- Escala de Likert con frecuencias, porcentajes, resumen descriptivo, recodificación inversa, puntuación media por dimensión y exportación CSV de frecuencias.

## Se conservan
Carga y biblioteca CSV, eliminación de archivos, limpieza y bitácora, perfil estadí­stico, correlaciones, graficos, DuckDB SQL y exportaciones CSV/Parquet/JSON.

## Interfaz
Fondo violeta más profundo y crédito visible: **Diseño: Ing. Hernán Quiroz**.

## Despliegue
1. Descomprime el ZIP y reemplaza los archivos del repositorio con esta versión.
2. Conserva la estructura `data/` y los CSV que necesites.
3. Verifica que `requirements.txt` está actualizado.
4. Haz commit en GitHub y espera el redeploy de Streamlit.

## Consideraciones metodológicas
El alfa de Cronbach no prueba por­ solo la validez ni la unidimensionalidad. Los i­tems deben pertenecer a un constructo interpretable. La recodificación inversa usa mí­nimo + máximo âˆ’ respuesta y presupone que todos los i­tems comparten el mismo rango. Para el análisis Likert, la media es un resumen descriptivo; considera también frecuencias y distribución ordinal. Las pruebas de hipótesis requieren verificar sus supuestos y el diseño muestral.


