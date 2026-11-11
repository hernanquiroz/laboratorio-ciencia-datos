[README.md](https://github.com/user-attachments/files/34695843/README.md)

# Laboratorio de Ciencia de Datos — versión 0.3.3

## Corrección de administración de archivos
- El botón de eliminación ahora usa un callback de Streamlit.
- Se elimina únicamente el archivo seleccionado en la biblioteca.
- La lista se actualiza en el rerun posterior.
- Se evita que el contenido que permanece en `file_uploader` vuelva a crear automáticamente el CSV recién eliminado.
- Se invalidan los datos de trabajo en sesión cuando se elimina la fuente activa.
- Se mantienen el diseño violeta, DuckDB, análisis, limpieza y exportaciones de la versión 0.3.2.

## Instalación
Reemplaza `app.py` y `README.md` en GitHub. No cambies `requirements.txt` ni borres `data/`.
Haz commit y espera el redeploy de Streamlit.

## Nota sobre el cargador
Si eliminas el mismo archivo que sigue visible en el cargador, la aplicación lo ignora para evitar recrearlo. Para volver a añadir ese mismo CSV, carga primero otro archivo y luego vuelve a seleccionar el CSV deseado.
