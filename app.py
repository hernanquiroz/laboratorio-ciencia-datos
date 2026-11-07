import hashlib, io, json, re
from datetime import datetime
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
STORE = ROOT / "data" / "csv_guardados"
STORE.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Laboratorio de Ciencia de Datos", page_icon="🔬", layout="wide")
st.markdown("""
<style>
.stApp{background:#F5F8F7;color:#263A45}
[data-testid="stSidebar"]{background:#EDF4F1;border-right:1px solid #DCE8E3}
.block-container{max-width:1500px;padding-top:1.5rem}
h1,h2,h3{color:#263A45;letter-spacing:-.02em}
[data-testid="stMetric"]{background:white;border:1px solid #DFE9E5;border-radius:14px;padding:14px}
[data-testid="stMetricValue"]{color:#267C78}
.stButton>button,.stDownloadButton>button{border-radius:10px;border:1px solid #B9D7CF;background:#F8FCFA;color:#246762}
.stButton>button[kind="primary"]{background:#267C78;color:white}
[data-testid="stTabs"] button[aria-selected="true"]{color:#267C78;border-bottom-color:#267C78}
.hero{background:linear-gradient(115deg,#E5F2EC,#EAF2F7);border:1px solid #D9E8E2;border-radius:17px;padding:20px 24px;margin-bottom:16px}
.hero p{color:#58717A;margin:0}
</style>""", unsafe_allow_html=True)

st.title("🔬 Laboratorio de Ciencia de Datos")
st.caption("Prototipo 0.3 · Python + DuckDB + Parquet + Streamlit")
st.markdown('<div class="hero"><h3>Explora, comprende y consulta tus datos</h3><p>Guarda y recupera CSV, examina variables, descubre relaciones estadísticas y ejecuta SQL.</p></div>', unsafe_allow_html=True)

def read_csv(raw):
    last = None
    for enc in ("utf-8-sig","utf-8","cp1252","latin1"):
        try:
            df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=enc)
            if len(df.columns)==1 and ";" in str(df.columns[0]):
                df = pd.read_csv(io.BytesIO(raw), sep=";", encoding=enc)
            return df
        except Exception as e: last=e
    raise ValueError(f"No se pudo interpretar el CSV: {last}")

def safe_stem(name):
    s = re.sub(r"[^A-Za-z0-9áéíóúÁÉÍÓÚñÑ_-]+","_",Path(name).stem).strip("_")
    return (s or "datos")[:75]

def nulls(df):
    return pd.DataFrame({"variable":df.columns,"tipo":[str(df[c].dtype) for c in df.columns],
      "nulos":[int(df[c].isna().sum()) for c in df.columns],
      "% nulos":[round(float(df[c].isna().mean()*100),2) for c in df.columns],
      "valores únicos":[int(df[c].nunique(dropna=True)) for c in df.columns]}).sort_values("% nulos",ascending=False)

def profile(df):
    rows=[]
    for c in df.select_dtypes(include="number").columns:
        s=df[c].dropna()
        if s.empty: continue
        q1,q3=s.quantile([.25,.75]); iqr=q3-q1
        out=int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum()) if iqr else 0
        rows.append({"variable":c,"media":s.mean(),"mediana":s.median(),
          "desviación estándar":s.std(),"mínimo":s.min(),"máximo":s.max(),"atípicos IQR":out})
    return pd.DataFrame(rows)

# Conexión DuckDB aislada por ejecución de Streamlit.
con=duckdb.connect(database=":memory:")

with st.sidebar:
    st.header("1. Biblioteca de archivos")
    uploaded=st.file_uploader("Añadir CSV",type=["csv"])
    if uploaded is not None:
        raw=uploaded.getvalue()
        digest=hashlib.sha256(raw).hexdigest()[:10]
        saved_path=STORE/f"{safe_stem(uploaded.name)}_{digest}.csv"
        if not saved_path.exists(): saved_path.write_bytes(raw)
        st.success(f"Guardado: {saved_path.name}")
    files=sorted(STORE.glob("*.csv"),key=lambda p:p.stat().st_mtime,reverse=True)
    if files:
        choice=st.selectbox("2. Volver a abrir un archivo",[p.name for p in files])
        chosen=STORE/choice
        if st.button("Eliminar archivo seleccionado",use_container_width=True):
            chosen.unlink(missing_ok=True); st.rerun()
    else:
        chosen=None
        st.info("Carga un CSV para comenzar.")
    st.divider()
    st.caption(f"{len(files)} archivo(s) en la biblioteca")
    st.caption("data/csv_guardados/")

try:
    if uploaded is not None:
        active=saved_path.name
        df=read_csv(raw)
    elif chosen is not None:
        active=chosen.name
        df=read_csv(chosen.read_bytes())
    else:
        st.info("Carga un archivo CSV desde la barra lateral.")
        st.stop()
    if len(df.columns)==0: raise ValueError("El CSV no contiene columnas.")
    cols=[str(c).strip() or f"columna_{i+1}" for i,c in enumerate(df.columns)]
    seen={}; unique=[]
    for c in cols:
        seen[c]=seen.get(c,0)+1
        unique.append(c if seen[c]==1 else f"{c}_{seen[c]}")
    df.columns=unique
    con.register("_df_source",df)
    try: con.execute("CREATE OR REPLACE TABLE datos AS SELECT * FROM _df_source").fetchall()
    finally: con.unregister("_df_source")
except Exception as e:
    st.error(f"No se pudo abrir el archivo: {e}"); st.stop()

n=con.execute("SELECT COUNT(*) FROM datos").fetchone()[0]
schema=con.execute("DESCRIBE datos").fetchdf()
preview=con.execute("SELECT * FROM datos LIMIT 2000").fetchdf()
nums=preview.select_dtypes(include="number").columns.tolist()
others=[c for c in preview.columns if c not in nums]
st.success(f"Archivo activo: {active}")
a,b,c,d=st.columns(4)
a.metric("Registros",f"{n:,}"); b.metric("Variables",len(df.columns))
c.metric("Numéricas",len(nums)); d.metric("Categóricas / otras",len(others))

tabs=st.tabs(["📋 Datos y estructura","🧪 Perfil estadístico","🔗 Correlaciones","📊 Gráficos","🧮 SQL DuckDB","📁 Archivos y exportación"])
with tabs[0]:
    st.subheader("Vista previa"); st.dataframe(preview,use_container_width=True,height=360)
    x,y=st.columns(2)
    with x: st.markdown("**Esquema DuckDB**"); st.dataframe(schema,use_container_width=True)
    with y: st.markdown("**Calidad de datos**"); st.dataframe(nulls(preview),use_container_width=True)
    st.caption("Vista previa de hasta 2.000 filas; SQL opera sobre la tabla completa.")
with tabs[1]:
    st.subheader("Estadística descriptiva automática")
    if nums:
        st.dataframe(profile(preview),use_container_width=True)
        st.markdown("**Resumen descriptivo**"); st.dataframe(preview[nums].describe().T,use_container_width=True)
        st.caption("Atípicos estimados con IQR (1,5 × rango intercuartílico); requieren interpretación.")
    else: st.info("No se detectaron variables numéricas.")
    if others:
        cat=st.selectbox("Frecuencias por categoría",others)
        freq=preview[cat].fillna("(sin dato)").astype(str).value_counts().head(30).rename_axis(cat).reset_index(name="frecuencia")
        st.dataframe(freq,use_container_width=True)
with tabs[2]:
    st.subheader("Matriz de correlaciones")
    if len(nums)>=2:
        corr=preview[nums].corr(numeric_only=True)
        fig=px.imshow(corr,text_auto=".2f",aspect="auto",zmin=-1,zmax=1,color_continuous_scale="Tealrose",title="Correlación de Pearson")
        st.plotly_chart(fig,use_container_width=True)
        st.caption("Correlación no implica causalidad. Pearson mide asociación lineal y puede ser sensible a valores atípicos.")
        mask=np.triu(np.ones(corr.shape,dtype=bool),k=1)
        pairs=corr.where(mask).stack().reset_index()
        if not pairs.empty:
            pairs.columns=["variable 1","variable 2","correlación"]
            pairs["magnitud"]=pairs["correlación"].abs()
            st.dataframe(pairs.sort_values("magnitud",ascending=False).head(20).drop(columns="magnitud"),use_container_width=True)
    else: st.info("Se necesitan al menos dos variables numéricas.")
with tabs[3]:
    st.subheader("Distribuciones y relaciones")
    if nums:
        col=st.selectbox("Variable para distribución",nums)
        st.plotly_chart(px.histogram(preview,x=col,nbins=25,marginal="box",title=f"Distribución de {col}"),use_container_width=True)
        if len(nums)>1:
            xx=st.selectbox("Variable X",nums,key="xx")
            yy=st.selectbox("Variable Y",[v for v in nums if v!=xx],key="yy")
            color=st.selectbox("Color por categoría",["(ninguno)"]+others)
            st.plotly_chart(px.scatter(preview,x=xx,y=yy,color=None if color=="(ninguno)" else color,title=f"{yy} frente a {xx}"),use_container_width=True)
    else: st.info("No hay columnas numéricas para graficar.")
with tabs[4]:
    st.subheader("Consultas SQL con DuckDB")
    st.caption("Tabla disponible: datos. Ejemplo: SELECT * FROM datos LIMIT 20")
    sql=st.text_area("Consulta SQL","SELECT * FROM datos LIMIT 20",height=130)
    if st.button("▶ Ejecutar consulta",type="primary"):
        try:
            result=con.execute(sql).fetchdf()
            st.session_state["v03_sql_result"]=result
            st.success(f"Consulta ejecutada: {len(result):,} filas.")
        except Exception as e: st.error(f"Error SQL: {e}")
    if "v03_sql_result" in st.session_state:
        st.dataframe(st.session_state["v03_sql_result"],use_container_width=True)
        st.download_button("Descargar resultado CSV",st.session_state["v03_sql_result"].to_csv(index=False).encode("utf-8-sig"),"resultado_sql.csv","text/csv")
with tabs[5]:
    st.subheader("Biblioteca de CSV")
    inventory=sorted(STORE.glob("*.csv"),key=lambda p:p.stat().st_mtime,reverse=True)
    if inventory:
        st.dataframe(pd.DataFrame([{"archivo":p.name,"tamaño KB":round(p.stat().st_size/1024,1),"modificado":datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")} for p in inventory]),use_container_width=True)
    else: st.info("No hay archivos guardados.")
    st.download_button("Descargar CSV activo",df.to_csv(index=False).encode("utf-8-sig"),"datos_activos.csv","text/csv")
    buf=io.BytesIO(); df.to_parquet(buf,index=False)
    st.download_button("Descargar Parquet activo",buf.getvalue(),"datos_activos.parquet","application/octet-stream")
    report={"version":"0.3","archivo":active,"fecha":datetime.now().isoformat(timespec="seconds"),"registros":int(n),"variables":[{"nombre":c,"tipo":str(df[c].dtype)} for c in df.columns],"nulos":{c:int(df[c].isna().sum()) for c in df.columns}}
    st.download_button("Descargar informe JSON",json.dumps(report,ensure_ascii=False,indent=2).encode("utf-8"),"informe_perfil.json","application/json")

st.divider()
st.caption("Prototipo 0.3 · Análisis exploratorio. Protege los CSV que contengan datos personales o sensibles.")
