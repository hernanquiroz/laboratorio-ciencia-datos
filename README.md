[README.md](https://github.com/user-attachments/files/34522759/README.md)
# Laboratorio de Ciencia de Datos — versión 0.3

## Funciones
- Interfaz clara y moderna: verde agua, azul suave y blanco cálido.
- Carga y almacenamiento de CSV en `data/csv_guardados/`.
- Selector para volver a abrir archivos y opción para eliminar.
- Perfil estadístico, tipos, nulos, cardinalidad y valores atípicos IQR.
- Matriz y ranking de correlaciones de Pearson.
- Histogramas, boxplots y diagramas de dispersión.
- Consultas SQL con DuckDB.
- Exportación CSV, Parquet e informe JSON.

## Instalación local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub y Streamlit
1. Descomprime el ZIP.
2. Reemplaza `app.py` y `requirements.txt` en tu repositorio.
3. Sube también `README.md` y la carpeta `data/csv_guardados/`.
4. Mantén `app.py` como archivo principal y espera el redeploy.

## Persistencia importante
La carpeta guarda los CSV dentro del disco de la aplicación. En Streamlit Community
Cloud ese disco no es persistencia garantizada: los archivos pueden desaparecer tras
reinicios, redeploys o recreación de la instancia. Para conservación duradera en la nube,
la siguiente fase debe conectar almacenamiento externo (S3 o compatible) usando Secrets.
No subas archivos con datos personales a un repositorio público.

## Límites
Vista previa y gráficos: máximo 2.000 filas. SQL: tabla completa. Correlación no implica
causalidad. El paquete no incluye el CSV original del usuario.
