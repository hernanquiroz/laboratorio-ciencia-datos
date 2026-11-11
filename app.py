import hashlib, io, json, re
from datetime import datetime
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT=Path(__file__).resolve().parent
STORE=ROOT/'data'/'csv_guardados'
DEMO=ROOT/'data'/'ejemplo_cambio_climatico_sintetico.csv'
STORE.mkdir(parents=True,exist_ok=True)
st.set_page_config(page_title='Laboratorio de Ciencia de Datos',page_icon='🔬',layout='wide')
st.markdown("""<style>
.stApp{background:#F7F4FB;color:#302B3D}
[data-testid="stSidebar"]{background:#F0EAF8;border-right:1px solid #E2D8EF}
.block-container{max-width:1500px;padding-top:1.5rem}
h1,h2,h3{color:#302B3D;letter-spacing:-.02em}
[data-testid="stMetric"]{background:#FFFFFF;border:1px solid #E7DFF0;border-radius:14px;padding:14px}
[data-testid="stMetricValue"]{color:#7860A8}
[data-testid="stMetricLabel"]{color:#756C82}
.stButton>button,.stDownloadButton>button{border-radius:10px;border:1px solid #D4C5E8;background:#FBF9FE;color:#5F4B83}
.stButton>button[kind="primary"]{background:#7860A8;color:white;border-color:#7860A8}
[data-testid="stTabs"] button[aria-selected="true"]{color:#7860A8;border-bottom-color:#7860A8}
.hero{background:linear-gradient(115deg,#EEE7F8,#F1ECFA);border:1px solid #E0D5EF;border-radius:17px;padding:20px 24px;margin-bottom:16px}
.hero p{color:#6D627D;margin:0}
[data-testid="stAlert"]{border-radius:12px}
.credit{position:fixed;bottom:18px;left:18px;font-size:12px;color:#766A88;background:#F8F5FC;border:1px solid #DED4EB;border-radius:10px;padding:7px 11px;z-index:999}
</style>""",unsafe_allow_html=True)
st.title('🔬 Laboratorio de Ciencia de Datos')
st.markdown('<div class="credit">Diseño Ing. Hernán Quiroz</div>', unsafe_allow_html=True)
st.caption('Prototipo 0.3.2 · SQL DuckDB corregido · interfaz violeta')
st.markdown('<div class="hero"><h3>De los datos originales al conocimiento</h3><p>Conserva la fuente original, revisa su calidad, documenta la limpieza y analiza una copia de trabajo.</p></div>',unsafe_allow_html=True)

def read_csv(raw):
    last=None
    for enc in ('utf-8-sig','utf-8','cp1252','latin1'):
        try:
            d=pd.read_csv(io.BytesIO(raw),sep=None,engine='python',encoding=enc)
            if len(d.columns)==1 and ';' in str(d.columns[0]): d=pd.read_csv(io.BytesIO(raw),sep=';',encoding=enc)
            return d
        except Exception as e: last=e
    raise ValueError(f'No se pudo interpretar el CSV: {last}')
def safe_stem(name):
    s=re.sub(r'[^A-Za-z0-9áéíóúÁÉÍÓÚñÑ_-]+','_',Path(name).stem).strip('_')
    return (s or 'datos')[:75]
def null_profile(d):
    return pd.DataFrame({'variable':d.columns,'tipo':[str(d[c].dtype) for c in d.columns], 'nulos':[int(d[c].isna().sum()) for c in d.columns],'% nulos':[round(float(d[c].isna().mean()*100),2) for c in d.columns],'únicos':[int(d[c].nunique(dropna=True)) for c in d.columns]}).sort_values('% nulos',ascending=False)
def stats_profile(d):
    out=[]
    for c in d.select_dtypes(include='number').columns:
        s=d[c].dropna()
        if s.empty: continue
        q1,q3=s.quantile([.25,.75]); iqr=q3-q1
        nout=int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum()) if iqr else 0
        out.append({'variable':c,'media':s.mean(),'mediana':s.median(),'desv. estándar':s.std(),'mínimo':s.min(),'máximo':s.max(),'atípicos IQR':nout})
    return pd.DataFrame(out)
def sql_single_statement(q):
    # Permitimos un único statement por ejecución para evitar que DuckDB reciba varios SELECT juntos.
    statements=[x.strip() for x in q.split(';') if x.strip()]
    if len(statements)!=1:
        raise ValueError('Ejecuta una sola consulta SQL por vez. Se detectaron '+str(len(statements))+' sentencias. Selecciona una consulta de ejemplo o deja solo un SELECT en el editor.')
    return statements[0]

def resolve_csv_paths_in_sql(query, active_path, active_original_name, store_dir):
    """Resuelve nombres CSV a rutas reales de la biblioteca local."""
    pattern = re.compile(r"(?i)(read_csv_auto|read_csv)\s*\(\s*(['\"])(.*?)\2")
    def replace_path(match):
        function, quote, requested = match.group(1), match.group(2), match.group(3)
        req = Path(requested)
        if req.is_absolute() and req.exists():
            resolved = req
        else:
            candidates = []
            direct = store_dir / req.name
            if direct.exists():
                candidates.append(direct)
            if req.name == Path(active_original_name).name or req.name == active_path.name:
                candidates.append(active_path)
            wanted = safe_stem(req.name).lower()
            for candidate in store_dir.glob("*.csv"):
                if safe_stem(candidate.name).lower().startswith(wanted):
                    candidates.append(candidate)
            resolved = next((p for p in candidates if p.exists()), None)
            if resolved is None:
                raise FileNotFoundError(
                    f"No se encontró '{requested}'. Archivo activo: '{active_path.name}'. "
                    "Usa la tabla `datos` (recomendado) o selecciona el CSV correcto."
                )
        escaped = str(resolved.resolve()).replace("'", "''")
        return f"{function}({quote}{escaped}{quote}"
    return pattern.sub(replace_path, query)

con=duckdb.connect(database=':memory:')
def delete_selected_csv():
    # Callback ejecutado antes de que Streamlit vuelva a renderizar la aplicación.
    filename = st.session_state.get('saved_csv_choice')
    if not filename:
        st.session_state['file_admin_message'] = ('error', 'No hay un archivo seleccionado.')
        return
    target = (STORE / Path(filename).name).resolve()
    if target.parent != STORE.resolve() or not target.is_file():
        st.session_state['file_admin_message'] = ('error', 'El archivo seleccionado ya no existe o no es válido.')
        return

    # Si el cargador todavía conserva exactamente ese archivo, no permitir
    # que el rerun lo vuelva a crear inmediatamente después de borrarlo.
    pending_upload = st.session_state.get('csv_uploader')
    if pending_upload is not None:
        pending_hash = hashlib.sha256(pending_upload.getvalue()).hexdigest()[:10]
        if target.name.endswith(f'_{pending_hash}.csv'):
            st.session_state['deleted_upload_hash'] = pending_hash

    target.unlink()
    st.session_state.pop('active_source', None)
    st.session_state.pop('clean_df', None)
    st.session_state.pop('clean_log', None)
    st.session_state['file_admin_message'] = ('success', f'Archivo eliminado: {target.name}')

with st.sidebar:
    st.header('1. Biblioteca de archivos')
    up=st.file_uploader('Añadir CSV',type=['csv'],key='csv_uploader')

    raw=None
    saved=None
    upload_is_deleted=False
    if up is not None:
        raw=up.getvalue()
        digest=hashlib.sha256(raw).hexdigest()[:10]
        if st.session_state.get('deleted_upload_hash') == digest:
            upload_is_deleted=True
            st.caption('Este archivo fue eliminado. Para volver a incorporarlo, carga otro archivo y después selecciónalo nuevamente.')
        else:
            saved=STORE/f'{safe_stem(up.name)}_{digest}.csv'
            if not saved.exists():
                saved.write_bytes(raw)
            st.success(f'Guardado: {saved.name}')

    admin_message=st.session_state.pop('file_admin_message',None)
    if admin_message:
        kind, message=admin_message
        if kind=='success': st.success(message)
        else: st.error(message)

    st.markdown('**Conjunto didáctico incluido**')
    use_demo=st.checkbox('Cargar ejemplo de cambio climático (sintético)',value=False,help='Datos simulados para probar el flujo. No son mediciones reales ni el CSV original que habías utilizado.')
    available=sorted(STORE.glob('*.csv'),key=lambda p:p.stat().st_mtime,reverse=True)
    if available:
        names=[p.name for p in available]
        current=st.session_state.get('saved_csv_choice')
        if current not in names:
            current=names[0]
        choice=st.selectbox('Volver a abrir un CSV guardado',names,index=names.index(current),key='saved_csv_choice')
        selected=STORE/choice
        st.button('Eliminar archivo seleccionado',use_container_width=True,on_click=delete_selected_csv)
    else:
        selected=None
        st.caption('La biblioteca está vacía.')
    st.divider()
    st.caption(f'{len(available)} archivo(s) guardados')
    st.caption('data/csv_guardados/')

# Si el archivo cargado se acaba de eliminar, no lo tratamos como fuente activa.
if upload_is_deleted:
    up=None
    raw=None
    saved=None

try:
    if up is not None and saved is not None: active=saved.name; active_path=saved; active_original_name=up.name; original=read_csv(raw); source_kind='Archivo recién cargado'
    elif use_demo: active=DEMO.name; active_path=DEMO; active_original_name=DEMO.name; original=pd.read_csv(DEMO); source_kind='Ejemplo sintético incluido'
    elif selected is not None and selected.exists(): active=selected.name; active_path=selected; active_original_name=selected.name; original=read_csv(selected.read_bytes()); source_kind='Biblioteca local'
    else: st.info('Carga un CSV, selecciona otro archivo guardado o activa el ejemplo sintético de cambio climático.'); st.stop()
    if original.shape[1]==0: raise ValueError('El CSV no contiene columnas.')
    original.columns=[str(c).strip() or f'columna_{i+1}' for i,c in enumerate(original.columns)]
    seen={}; names=[]
    for c in original.columns:
        seen[c]=seen.get(c,0)+1; names.append(c if seen[c]==1 else f'{c}_{seen[c]}')
    original.columns=names
except Exception as e: st.error(f'No se pudo abrir el archivo: {e}'); st.stop()

# Guardamos el original en sesión y derivamos la tabla limpia sin sobrescribirlo.
if st.session_state.get('active_source')!=active:
    st.session_state['active_source']=active
    st.session_state['clean_df']=original.copy(deep=True)
    st.session_state['clean_log']=[]
clean=st.session_state['clean_df']
con.register('_source',clean)
try: con.execute('CREATE OR REPLACE TABLE datos AS SELECT * FROM _source').fetchall()
finally: con.unregister('_source')
n=len(clean); numeric=clean.select_dtypes(include='number').columns.tolist(); other=[c for c in clean.columns if c not in numeric]
st.success(f'Fuente activa: {active} · {source_kind}')
a,b,c,d=st.columns(4); a.metric('Registros',f'{n:,}'); b.metric('Variables',len(clean.columns)); c.metric('Numéricas',len(numeric)); d.metric('Celdas vacías',int(clean.isna().sum().sum()))

tabs=st.tabs(['📋 Datos y estructura','🧹 Ciclo de vida y limpieza','🧪 Perfil estadístico','🔗 Correlaciones','📊 Gráficos','🧮 SQL DuckDB','📁 Archivos y exportación'])
with tabs[0]:
    st.subheader('Vista previa de la tabla de trabajo'); st.dataframe(clean.head(2000),use_container_width=True,height=350)
    x,y=st.columns(2)
    with x: st.markdown('**Esquema DuckDB**'); st.dataframe(con.execute('DESCRIBE datos').fetchdf(),use_container_width=True)
    with y: st.markdown('**Calidad inicial / actual**'); st.dataframe(null_profile(clean),use_container_width=True)
    st.caption('La tabla SQL `datos` refleja la copia de trabajo actual. El archivo fuente original se conserva sin modificar.')
with tabs[1]:
    st.subheader('Ciclo de vida de los datos')
    st.markdown('**1. Ingesta → 2. Perfilado → 3. Limpieza → 4. Validación → 5. Transformación → 6. Análisis → 7. Exportación y documentación.**')
    st.info('Buenas prácticas: no se limpia a ciegas ni se sobrescribe el original. Primero se diagnostica, luego se decide cada tratamiento según el significado de las variables.')
    st.markdown('**Diagnóstico antes de limpiar**'); st.dataframe(null_profile(original),use_container_width=True)
    st.markdown('**Acciones controladas sobre la copia de trabajo**')
    trim=st.checkbox('Quitar espacios al inicio/final de textos',value=True)
    blanks=st.checkbox('Convertir textos vacíos o solo espacios en valores nulos',value=True)
    dedup=st.checkbox('Eliminar filas duplicadas exactas',value=False)
    numeric_cols=clean.select_dtypes(include='number').columns.tolist()
    missing_mode=st.selectbox('Tratamiento de valores faltantes', ['No imputar (conservar nulos)','Eliminar filas con algún nulo','Imputar numéricas con mediana y categóricas con moda'])
    outlier_mode=st.selectbox('Tratamiento de atípicos', ['Solo detectar (recomendado)','No aplicar tratamiento','Recortar numéricas a límites IQR (1,5×IQR)'])
    col_a,col_b=st.columns(2)
    with col_a:
        if st.button('Aplicar limpieza seleccionada',type='primary'):
            work=original.copy(deep=True); log=[]
            if trim:
                for col in work.select_dtypes(include=['object','string']).columns: work[col]=work[col].map(lambda v:v.strip() if isinstance(v,str) else v)
                log.append('Se recortaron espacios en campos de texto.')
            if blanks:
                for col in work.select_dtypes(include=['object','string']).columns: work[col]=work[col].replace(r'^\s*$',np.nan,regex=True)
                log.append('Textos vacíos convertidos en nulos.')
            if dedup:
                before=len(work); work=work.drop_duplicates().copy(); log.append(f'Se eliminaron {before-len(work)} filas duplicadas exactas.')
            if missing_mode.startswith('Eliminar'):
                before=len(work); work=work.dropna().copy(); log.append(f'Se eliminaron {before-len(work)} filas con al menos un nulo.')
            elif missing_mode.startswith('Imputar'):
                for col in work.columns:
                    if pd.api.types.is_numeric_dtype(work[col]):
                        if work[col].notna().any(): work[col]=work[col].fillna(work[col].median())
                    else:
                        mode=work[col].mode(dropna=True)
                        if not mode.empty: work[col]=work[col].fillna(mode.iloc[0])
                log.append('Nulos imputados con mediana (numéricas) y moda (otras).')
            if outlier_mode.startswith('Recortar'):
                for col in work.select_dtypes(include='number').columns:
                    q1,q3=work[col].quantile([.25,.75]); iqr=q3-q1
                    if pd.notna(iqr) and iqr>0: work[col]=work[col].clip(q1-1.5*iqr,q3+1.5*iqr)
                log.append('Valores numéricos recortados a límites IQR.')
            else: log.append('Atípicos no modificados; se mantienen para análisis.')
            st.session_state['clean_df']=work; st.session_state['clean_log']=log; st.rerun()
    with col_b:
        if st.button('Restaurar copia de trabajo desde el original'):
            st.session_state['clean_df']=original.copy(deep=True); st.session_state['clean_log']=[]; st.rerun()
    if st.session_state.get('clean_log'):
        st.markdown('**Bitácora de limpieza**')
        for item in st.session_state['clean_log']: st.write('• '+item)
    st.markdown('**Comparación de registros**')
    st.write(f'Original: {len(original):,} · Copia de trabajo: {len(clean):,} · Diferencia: {len(original)-len(clean):,}')
    st.dataframe(null_profile(clean),use_container_width=True)
    st.download_button('Descargar copia limpia CSV',clean.to_csv(index=False).encode('utf-8-sig'),'datos_limpios.csv','text/csv')
    st.caption('Importante: imputar o recortar puede introducir sesgos. Verifica unidades, rangos plausibles, fechas, códigos y contexto antes de aceptar cambios.')
with tabs[2]:
    st.subheader('Perfil estadístico automático')
    if numeric:
        st.dataframe(stats_profile(clean),use_container_width=True); st.dataframe(clean[numeric].describe().T,use_container_width=True)
    else: st.info('No se detectaron columnas numéricas. Revisa tipos de datos.')
    if other:
        cat=st.selectbox('Frecuencias categóricas',other); freq=clean[cat].fillna('(sin dato)').astype(str).value_counts().head(30).rename_axis(cat).reset_index(name='frecuencia'); st.dataframe(freq,use_container_width=True)
with tabs[3]:
    st.subheader('Matriz de correlaciones')
    if len(numeric)>=2:
        corr=clean[numeric].corr(numeric_only=True); st.plotly_chart(px.imshow(corr,text_auto='.2f',aspect='auto',zmin=-1,zmax=1,color_continuous_scale='Tealrose'),use_container_width=True)
        st.caption('Correlación no implica causalidad. Pearson evalúa asociación lineal.')
    else: st.info('Se requieren al menos dos variables numéricas.')
with tabs[4]:
    st.subheader('Distribuciones y relaciones')
    if numeric:
        v=st.selectbox('Variable para distribución',numeric); st.plotly_chart(px.histogram(clean,x=v,nbins=25,marginal='box'),use_container_width=True)
        if len(numeric)>1:
            xx=st.selectbox('Variable X',numeric,key='plot_x'); yy=st.selectbox('Variable Y',[c for c in numeric if c!=xx],key='plot_y'); st.plotly_chart(px.scatter(clean,x=xx,y=yy),use_container_width=True)
    else: st.info('No hay variables numéricas.')
with tabs[5]:
    st.subheader('Consultas SQL con DuckDB')
    st.caption('La tabla `datos` ya contiene el archivo activo. Consulta esta tabla sin indicar rutas.')
    examples={
        'Primeras 10 filas':'SELECT * FROM datos LIMIT 10',
        'Contar registros':'SELECT COUNT(*) AS total_registros FROM datos',
        'Ver columnas y tipos':'DESCRIBE datos',
        'Leer el CSV activo por ruta (compatibilidad)':'SELECT * FROM read_csv_auto(\'ARCHIVO_ACTIVO.csv\') LIMIT 10'
    }
    ex=st.selectbox('Cargar consulta de ejemplo',list(examples),key='sql_example')
    default_sql=examples[ex]
    if ex=='Leer el CSV activo por ruta (compatibilidad)':
        default_sql=f"SELECT * FROM read_csv_auto('{active_original_name.replace(chr(39), chr(39)*2)}') LIMIT 10"
    sql=st.text_area('Consulta SQL',default_sql,height=145,key='sql_editor')
    st.caption('Recomendación: usa `FROM datos`. Si utilizas `read_csv_auto(\'nombre.csv\')`, se intentará localizar el archivo en la biblioteca y resolver su ruta.')
    if st.button('▶ Ejecutar consulta',type='primary'):
        try:
            statement=sql_single_statement(sql)
            statement=resolve_csv_paths_in_sql(statement,active_path,active_original_name,STORE)
            result=con.execute(statement).fetchdf()
            st.session_state['sql_result']=result
            st.session_state['sql_error']=None
        except Exception as e:
            st.session_state['sql_error']=str(e)
    if st.session_state.get('sql_error'):
        st.error('No se pudo ejecutar la consulta: '+st.session_state['sql_error'])
    if 'sql_result' in st.session_state:
        st.dataframe(st.session_state['sql_result'],use_container_width=True)
        st.download_button('Descargar resultado SQL',st.session_state['sql_result'].to_csv(index=False).encode('utf-8-sig'),'resultado_sql.csv','text/csv')
with tabs[6]:
    st.subheader('Archivos y exportación')
    inv=sorted(STORE.glob('*.csv'),key=lambda p:p.stat().st_mtime,reverse=True)
    if inv: st.dataframe(pd.DataFrame([{'archivo':p.name,'tamaño KB':round(p.stat().st_size/1024,1)} for p in inv]),use_container_width=True)
    else: st.info('No hay archivos CSV guardados por el usuario.')
    st.download_button('Exportar copia de trabajo CSV',clean.to_csv(index=False).encode('utf-8-sig'),'datos_trabajo.csv','text/csv')
    pb=io.BytesIO(); clean.to_parquet(pb,index=False); st.download_button('Exportar copia de trabajo Parquet',pb.getvalue(),'datos_trabajo.parquet','application/octet-stream')
    report={'version':'0.3.2','fuente':active,'fecha':datetime.now().isoformat(timespec='seconds'),'filas_originales':len(original),'filas_trabajo':len(clean),'columnas':list(clean.columns),'bitacora_limpieza':st.session_state.get('clean_log',[]),'nulos_actuales':{c:int(clean[c].isna().sum()) for c in clean.columns}}
    st.download_button('Exportar informe JSON',json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8'),'informe_calidad_limpieza.json','application/json')
st.divider(); st.caption('Prototipo 0.3.2 · Análisis exploratorio. El ejemplo climático incluido es sintético, no representa mediciones observadas.')

