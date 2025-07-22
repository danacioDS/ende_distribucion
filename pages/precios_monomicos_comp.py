import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Configuración de la página
st.set_page_config(page_title="Dashboard de Precios de Energía", layout="wide")
st.title("Análisis Integral de Precios de Energía")

@st.cache_data
def load_and_transform_data():
    try:
        current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
        file_path = current_dir / "data" / "serie_precios_sin_outliers.xlsx"

        if not file_path.exists():
            st.error("Archivo no encontrado")
            return None

        # Cargar datos
        df = pd.read_excel(file_path, engine="openpyxl")
        if df.empty:
            st.error("El archivo está vacío")
            return None

        # Estandarizar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Mostrar columnas reales para diagnóstico
        st.sidebar.write("Columnas en el archivo:", df.columns.tolist())
        
        # Verificar columnas requeridas con flexibilidad
        required_mappings = {
            'agente': ['AGENTE', 'AGENT'],
            'empresa': ['EMPRESA', 'COMPANY'],
            'mes': ['MES', 'MONTH', 'PERIODO'],
            'precio': ['PRECIO_MONOMICO', 'PRECIO', 'PRICE']
        }
        
        # Buscar coincidencias para cada campo requerido
        found_columns = {}
        for key, options in required_mappings.items():
            for option in options:
                if option in df.columns:
                    found_columns[key] = option
                    break
        
        # Verificar si se encontraron todas las columnas requeridas
        if len(found_columns) != 4:
            missing = [k for k in required_mappings if k not in found_columns]
            st.error(f"Columnas requeridas faltantes: {missing}")
            return None

        # Renombrar columnas a nombres estandarizados
        df = df.rename(columns={
            found_columns['agente']: 'AGENTE',
            found_columns['empresa']: 'EMPRESA',
            found_columns['mes']: 'MES',
            found_columns['precio']: 'PRECIO_MONOMICO'
        })
        
        # Convertir MES a formato de fecha
        df['FECHA'] = pd.to_datetime(
            df['MES'].astype(str).str.strip(),
            format='%m%Y',
            errors='coerce'
        )
        
        # Manejar formato alternativo (ej: "012023" -> enero 2023)
        if df['FECHA'].isnull().any():
            df.loc[df['FECHA'].isnull(), 'FECHA'] = pd.to_datetime(
                df.loc[df['FECHA'].isnull(), 'MES'].astype(str).str.strip(),
                format='%d%m%Y',
                errors='coerce'
            )
        
        # Normalizar fechas al primer día del mes
        df['FECHA'] = df['FECHA'].dt.to_period('M').dt.to_timestamp()
        
        # Convertir precio a numérico
        df['Precio Monómico USD/MWh'] = pd.to_numeric(
            df['PRECIO_MONOMICO'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        
        # Crear columna de periodo (formato MES/AAAA)
        df['Periodo'] = df['FECHA'].dt.strftime('%m/%Y')
        
        # Eliminar filas con valores faltantes
        df = df.dropna(subset=['FECHA', 'Precio Monómico USD/MWh'])
        
        return df[['AGENTE', 'EMPRESA', 'FECHA', 'Precio Monómico USD/MWh', 'Periodo']]

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

# Cargar datos
df = load_and_transform_data()
if df is None:
    st.stop()

# Sidebar para filtros
st.sidebar.title("Filtros y Configuración")

# Manejo de fechas
if 'FECHA' in df.columns:
    min_date = df['FECHA'].min()
    max_date = df['FECHA'].max()
    
    # Verificar fechas válidas
    if pd.isna(min_date) or pd.isna(max_date):
        st.sidebar.warning("No hay fechas válidas en los datos. Usando rango por defecto.")
        min_date = datetime(2023, 1, 1)
        max_date = datetime.now()
    
    min_ts = min_date.timestamp()
    max_ts = max_date.timestamp()

    selected_range = st.sidebar.slider(
        "Seleccionar rango de fechas",
        min_value=min_ts,
        max_value=max_ts,
        value=(min_ts, max_ts),
        format="YYYY-MM-DD"
    )

    date_range = [
        datetime.fromtimestamp(selected_range[0]),
        datetime.fromtimestamp(selected_range[1])
    ]

    df_filtered = df[(df['FECHA'] >= date_range[0]) & (df['FECHA'] <= date_range[1])]
else:
    st.sidebar.warning("No se encontró la columna 'FECHA' en los datos.")
    df_filtered = df

# Selección de empresa y agente
empresas = df_filtered['EMPRESA'].unique()
selected_empresa = st.sidebar.selectbox("Seleccionar Empresa", empresas)

agentes_disponibles = df_filtered[df_filtered['EMPRESA'] == selected_empresa]['AGENTE'].unique()
selected_agente = st.sidebar.selectbox("Seleccionar Agente", agentes_disponibles)

# Layout
tab1, tab2 = st.tabs(["Visión Detallada", "Visión de Promedios"])

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(f"Evolución de Precios para Agente: {selected_agente}")
        df_agente = df_filtered[df_filtered['AGENTE'] == selected_agente]
        precio_promedio_agente = df_agente['Precio Monómico USD/MWh'].mean()

        fig_agente = px.line(
            df_agente,
            x='FECHA',
            y='Precio Monómico USD/MWh',
            title=f"Precios para {selected_agente}",
            markers=True,
            line_shape='linear'
        )
        fig_agente.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_agente.update_layout(yaxis_title="Precio Monómico USD/MWh", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_agente, use_container_width=True)

        st.metric(label=f"Precio Promedio {selected_agente}", value=f"{precio_promedio_agente:.2f} US$/MWh")

    with col_right:
        st.subheader(f"Precio Promedio para Empresa: {selected_empresa}")
        df_empresa = df_filtered[df_filtered['EMPRESA'] == selected_empresa]
        df_empresa_prom = df_empresa.groupby(['FECHA', 'EMPRESA'])['Precio Monómico USD/MWh'].mean().reset_index()
        precio_promedio_empresa = df_empresa['Precio Monómico USD/MWh'].mean()

        fig_empresa = px.line(
            df_empresa_prom,
            x='FECHA',
            y='Precio Monómico USD/MWh',
            title=f"Precio Promedio para {selected_empresa}",
            markers=True,
            line_shape='spline'
        )
        fig_empresa.update_traces(line=dict(width=3, dash='dot'), marker=dict(size=8, symbol='diamond'))
        fig_empresa.update_layout(yaxis_title="Precio Monómico Promedio (USD/MWh)", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_empresa, use_container_width=True)

        cols_empresa = st.columns(2)
        with cols_empresa[0]:
            st.metric(label=f"Promedio {selected_empresa}", value=f"{precio_promedio_empresa:.2f} USD/MWh")

    # Evolución del Precio Promedio del Sistema
    st.subheader("Evolución del Precio Promedio del Sistema")
    df_sistema = df_filtered.groupby('FECHA')['Precio Monómico USD/MWh'].mean().reset_index()
    df_sistema['Precio Monómico USD/MWh'] = df_sistema['Precio Monómico USD/MWh'].round(2)
    precio_promedio_sistema = df_sistema['Precio Monómico USD/MWh'].mean()

    fig_sistema = px.bar(
        df_sistema,
        x='FECHA',
        y='Precio Monómico USD/MWh',
        title="Evolución del Precio Promedio del Sistema",
        text_auto=True,
        color='Precio Monómico USD/MWh',
        color_continuous_scale=px.colors.sequential.Blugrn,
    )
    
    fig_sistema.update_traces(
        textposition='inside',
        textfont=dict(size=18, color='white'))
    
    fig_sistema.update_layout(yaxis_title="Precio Monómico Promedio (USD/MWh)", xaxis_title="Fecha", showlegend=False, bargap=0.2)
    st.plotly_chart(fig_sistema, use_container_width=True)

    st.metric(label="Precio Promedio del Sistema", value=f"{precio_promedio_sistema:.2f} USD/MWh")

with tab2:
    st.header("Análisis Comparativo")
    st.subheader("Comparación de Empresas")

    df_empresas_prom_tab2 = df_filtered.groupby(['FECHA', 'EMPRESA'])['Precio Monómico USD/MWh'].mean().reset_index()
    fig_comparacion = px.line(
        df_empresas_prom_tab2,
        x='FECHA',
        y='Precio Monómico USD/MWh',
        color='EMPRESA',
        line_dash='EMPRESA',
        symbol='EMPRESA',
        title="Comparación de Precios Promedio por Empresa"
    )
    fig_comparacion.update_layout(
        yaxis_title="Precio Monómico Promedio (USD/MWh)",
        xaxis_title="Fecha",
        legend_title="Empresas"
    )
    st.plotly_chart(fig_comparacion, use_container_width=True)

    st.subheader("Métricas Clave")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precio Mínimo Sistema", f"{df_filtered['Precio Monómico USD/MWh'].min():.2f} USD/MWh")
    with col2:
        st.metric("Precio Promedio Sistema", f"{df_filtered['Precio Monómico USD/MWh'].mean():.2f} USD/MWh")
    with col3:
        st.metric("Precio Máximo Sistema", f"{df_filtered['Precio Monómico USD/MWh'].max():.2f} USD/MWh")

# Sidebar: información del sistema
st.sidebar.markdown("---")
st.sidebar.subheader("Información del Sistema")
st.sidebar.write(f"Total de agentes: {df_filtered['AGENTE'].nunique()}")
st.sidebar.write(f"Total de empresas: {df_filtered['EMPRESA'].nunique()}")
if 'FECHA' in df_filtered.columns:
    min_date = df_filtered['FECHA'].min().strftime('%Y-%m-%d')
    max_date = df_filtered['FECHA'].max().strftime('%Y-%m-%d')
    st.sidebar.write(f"Rango de fechas: {min_date} a {max_date}")