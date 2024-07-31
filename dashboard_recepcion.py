#dashboard_recepcion.py
import numpy as np
import streamlit as st
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
#lxml

st.set_page_config(layout='wide')
weights=[1,4,1]
col1, col2, col3=st.columns(weights)
st.markdown("""
    <div style="text-align: center;">
        <h1>Dashboard uso scanner</h1>
    </div>
""", unsafe_allow_html=True)
@st.cache_data
#https://docs.google.com/spreadsheets/d/e/2PACX-1vSTgVotKr2F-mmQYNhuwB2AIYgup3lPMikmoluvo0ekSgMScblFhjPxRIrYuWB8uQ/pubhtml
def load_data():
    url='https://docs.google.com/spreadsheets/d/e/2PACX-1vSTgVotKr2F-mmQYNhuwB2AIYgup3lPMikmoluvo0ekSgMScblFhjPxRIrYuWB8uQ/pubhtml'
    html=pd.read_html(url, header=2)
    df=html[0]
    df=df.dropna(subset=['PROVEEDOR'])
    
    return df

df=load_data()
df=df.drop(columns=['2','N','CITA','ORDEN PEDIDO','TARIMAS'])
df['FECHA DE DESCARGA']=df['FECHA DE DESCARGA'] = pd.to_datetime(df['FECHA DE DESCARGA'])
df['INICIO'] = pd.to_datetime(df['INICIO'], format='%I:%M:%S %p').dt.time
df['TERMINO'] = pd.to_datetime(df['TERMINO'], format='%I:%M:%S %p').dt.time
df['MONTO'] = df['MONTO'].replace('[-\s]+', '', regex=True).replace('', np.nan)
#df['MONTO'] = df['MONTO'].replace('', regex=True).replace('', np.nan)
df['MONTO'] = df['MONTO'].replace('[\$,]', '', regex=True)
df=df.dropna(subset=['MONTO'])
df['MONTO'].replace('', np.nan, inplace=True)
df=df.dropna(subset=['MONTO'])
df['MONTO'] = df['MONTO'].astype(float)
def calcular_duracion(inicio, termino):
    fecha_inicio = pd.to_datetime(inicio, format='%H:%M:%S')
    fecha_termino = pd.to_datetime(termino, format='%H:%M:%S')
    if fecha_termino < fecha_inicio:
            fecha_termino += pd.DateOffset(days=1)
        
        # Calcular la diferencia
    duracion = fecha_termino - fecha_inicio
    return duracion
df['Duracion'] = df.apply(lambda row: calcular_duracion(row['INICIO'], row['TERMINO']), axis=1)
df['Duracion'] = df['Duracion'].dt.total_seconds() / 60
df['tiempo_util']=0
df.loc[df['Duracion']>0,'tiempo_util']=1
df.loc[df['TIPO DE UNIDAD']=='IZUZU','TIPO DE UNIDAD']='ISUZU'
df['TIPO DE UNIDAD']=df['TIPO DE UNIDAD'].str.upper()
fecha_min=df['FECHA DE DESCARGA'].min().date()
fecha_max=df['FECHA DE DESCARGA'].max().date()
start_date=st.sidebar.date_input('Fecha de inicio', value=fecha_min, min_value=fecha_min, max_value=fecha_max)
end_date=st.sidebar.date_input('Fecha de final', value=fecha_max, min_value=fecha_min, max_value=fecha_max)
df=df[(df['FECHA DE DESCARGA']>=pd.to_datetime(start_date))&(df['FECHA DE DESCARGA']<=pd.to_datetime(end_date))]
filtro_proveedores=st.sidebar.multiselect('Filtro por proveedor',df['PROVEEDOR'].unique())
filtro_bodeguero=st.sidebar.multiselect('Filtro por bodeguero',df['BODEGUERO'].unique())
filtro_comprador=st.sidebar.multiselect('Filtro por comprador',df['COMPRADOR'].unique())
filtro_unidad=st.sidebar.multiselect('Filtro por tipo de unidad',df['TIPO DE UNIDAD'].unique())

if filtro_bodeguero:
    df = df[df['BODEGUERO'].isin(filtro_bodeguero)]

if filtro_comprador:
    df = df[df['COMPRADOR'].isin(filtro_comprador)]

if filtro_proveedores:
    df = df[df['PROVEEDOR'].isin(filtro_proveedores)]

if filtro_unidad:
    df = df[df['TIPO DE UNIDAD'].isin(filtro_unidad)]

df['VoF']=df['VoF'].astype(float)
uso_scanner=df['VoF'].sum()
conteo=df['TIPO DE UNIDAD'].count()
porcentaje_uso=round(((uso_scanner/conteo)*100),2)
porcentaje_max=100
color_gauge='#522d6d'
color_gray='#e5e1e6'
color_threshold='red'
fig = go.Figure(go.Indicator(
    mode='gauge+number',
    value=porcentaje_uso,
    title={'text': 'Indicador de uso'},
    gauge={
        'axis': {'range': [0, porcentaje_max]},
        'bar': {'color': color_gauge},
        'steps': [
            {'range': [0, 100], 'color': color_gray}
        ],
        'threshold': {
            'line': {'color': color_threshold, 'width': 5},
            'thickness': 0.75,
            
        }
    }
))

weights=[1,4,1]
col1, col2, col3=st.columns(weights)
with col2:
    st.plotly_chart(fig)

df_uso=df[df['VoF']==1]

uso=df_uso.groupby('BODEGUERO')['VoF'].sum().reset_index()
uso['conteo_uso_app']=uso['VoF']
uso=uso.drop(columns=['VoF'])
uso = uso[uso['conteo_uso_app'] > 10].reset_index()
uso=uso.drop(columns=['index'])
#df_no_uso=df.groupby('PROVEEDOR')['']

df_no_uso=df[df['VoF']==0]
no_uso=df_no_uso.groupby('BODEGUERO')['VoF'].count().reset_index()
no_uso['conteo_uso_app']=no_uso['VoF']
no_uso=no_uso.drop(columns=['VoF'])
no_uso = no_uso[no_uso['conteo_uso_app'] > 10].reset_index()
no_uso=no_uso.drop(columns=['index'])

columna1, columna2 = st.columns(2)

with columna1:
    st.markdown("<h2 style='color: green;'>Bodegueros que usan el scanner </h2>", unsafe_allow_html=True)
    uso

with columna2:
    st.markdown("<h2 style='color: red;'>Bodegueros que no usan el scanner </h2>", unsafe_allow_html=True)
    no_uso

df['Mes'] = df['FECHA DE DESCARGA'].dt.to_period('M') 
conteo_por_mes_COMPRADOR = df.groupby(['Mes', 'COMPRADOR']).size().unstack(fill_value=0)
conteo_por_mes_COMPRADOR = round(conteo_por_mes_COMPRADOR.mean(axis=0))

conteo_por_mes_PROVEEDOR = df.groupby(['Mes', 'PROVEEDOR']).size().unstack(fill_value=0)
conteo_por_mes_PROVEEDOR = round(conteo_por_mes_PROVEEDOR.mean(axis=0))
#conteo_por_mes_COMPRADOR=conteo_por_mes_COMPRADOR.drop(columns=[1], axis=1)
#Monto=round(df['MONTO'].sum())
#Monto
#df

colum1, colum2 = st.columns(2)
with colum1:
    st.markdown("<h2 style='color: black;'>Promedio de compras por comprador </h2>", unsafe_allow_html=True)
    conteo_por_mes_COMPRADOR

with colum2:
    st.markdown("<h2 style='color: black;'>Promedio de compras por proveedor </h2>", unsafe_allow_html=True)
    conteo_por_mes_PROVEEDOR  

conteo_por_mes_PROVEEDOR = df.groupby(['Mes', 'PROVEEDOR']).size().unstack(fill_value=0).reset_index()
conteo_por_mes_PROVEEDOR = conteo_por_mes_PROVEEDOR.melt(id_vars=['Mes'], var_name='proveedor', value_name='Conteo')
conteo_por_mes_PROVEEDOR.columns = conteo_por_mes_PROVEEDOR.columns.astype(str)
conteo_por_mes_PROVEEDOR['Conteo'] = pd.to_numeric(conteo_por_mes_PROVEEDOR['Conteo'], errors='coerce')
conteo_por_mes_PROVEEDOR['Mes'] = conteo_por_mes_PROVEEDOR['Mes'].dt.to_timestamp()

nombres_unicos = conteo_por_mes_PROVEEDOR['proveedor'].unique()

cols = st.columns(3)

for i, nombre in enumerate(nombres_unicos):
    group = conteo_por_mes_PROVEEDOR[conteo_por_mes_PROVEEDOR['proveedor'] == nombre]
    fig, ax = plt.subplots()
    ax.plot(group['Mes'], group['Conteo'], label=nombre, marker='o')
    ax.set_title(nombre, color='#a7a1c2')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Conteo de Uso')
    ax.tick_params(axis='x', colors='#a7a1c2')
    ax.tick_params(axis='y', colors='#a7a1c2')
    ax.set_facecolor('none')
    fig.patch.set_alpha(0)
    plt.xticks(rotation=90)

    # Mostrar el gráfico en la columna correspondiente
    cols[i % 3].pyplot(fig)
