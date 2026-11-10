[README.md](https://github.com/user-attachments/files/34638931/README.md)

# Laboratorio de Ciencia de Datos — versión 0.3.2

## Cambios
- Interfaz de fondo violeta suave/lavanda con superficies claras.
- Crédito lateral: **Diseño Ing. Hernán Quiroz**.
- Resolución de rutas en `read_csv_auto('nombre.csv')` y `read_csv('nombre.csv')` para archivos guardados en la biblioteca.
- Consultas SQL de ejemplo y recomendación de usar la tabla `datos`, que ya contiene el archivo activo.
- Mantiene el ciclo de vida, perfilado, limpieza sobre copia, bitácora y exportaciones.

## Ejemplos SQL
```sql
SELECT * FROM datos LIMIT 10;
SELECT COUNT(*) AS total_registros FROM datos;
DESCRIBE datos;
```

## Actualización
1. Descomprime el ZIP.
2. Reemplaza `app.py`, `requirements.txt` y `README.md` en GitHub.
3. Conserva la carpeta `data/` y sus archivos.
4. Haz commit y espera el redeploy.

## Nota
La forma recomendada de consultar el CSV activo es usar `FROM datos`, sin ruta de archivo.
El disco local de Streamlit Community Cloud no garantiza persistencia entre reinicios.
