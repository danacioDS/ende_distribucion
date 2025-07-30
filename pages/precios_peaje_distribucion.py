import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Configuración de la página
st.set_page_config(page_title="Dashboard de Peaje de Generacion", layout="wide")
st.title("Análisis Integral de Peajes de Generación")

@st.cache_data
def load_and_transform_data():
    try:
        current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
        file_path = current_dir / "data" / "serie_peaje.xlsx"

        if not file_path.exists():
            st.error("Archivo no encontrado")
            return None

        df = pd.read_excel(file_path, engine="openpyxl")
        if df.empty:
            st.error("El archivo está vacío")
            return None

        df.columns = df.columns.str.strip()
        price_columns = [col for col in df.columns if "Peaje generación USD/MWh" in col]

        dfs = []
        for col in price_columns:
            # Extraer el código de fecha (última palabra en el nombre de la columna)
            period_code = col.split()[-1].strip()
            
            # Convertir código MES/AÑO a fecha
            try:
                # Mes es siempre los primeros dígitos (1-2 caracteres)
                # Año es el resto (4 caracteres para años completos)
                if len(period_code) == 5:  # Ej: "10224" sería octubre 2024? -> pero debería ser 102024
                    # Asumir formato MYYYY (M=1 dígito, YYYY=4 dígitos)
                    month = int(period_code[0])
                    year = int(period_code[1:5])
                elif len(period_code) == 6:  # Formato correcto MMYYYY
                    month = int(period_code[0:2])
                    year = int(period_code[2:6])
                else:
                    continue  # Saltar formatos desconocidos
                
                date = datetime(year, month, 1)
            except Exception as e:
                st.warning(f"Error convirtiendo periodo {period_code}: {str(e)}")
                continue

            temp_df = df[['AGENTE', 'EMPRESA', col]].copy()
            temp_df['FECHA'] = date
            temp_df['Peaje generación USD/MWh'] = pd.to_numeric(
                temp_df[col].astype(str).str.replace(',', ''), 
                errors='coerce'
            )
            temp_df['Periodo'] = period_code
            dfs.append(temp_df)

        if not dfs:
            st.error("No se pudieron procesar columnas de precios")
            return None
            
        transformed_df = pd.concat(dfs)
        transformed_df = transformed_df.dropna(subset=['FECHA', 'Peaje generación USD/MWh'])

        return transformed_df

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
        precio_promedio_agente = df_agente['Peaje generación USD/MWh'].mean()

        fig_agente = px.line(
            df_agente,
            x='FECHA',
            y='Peaje generación USD/MWh',
            title=f"Precios para {selected_agente}",
            markers=True,
            line_shape='linear'
        )
        fig_agente.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_agente.update_layout(yaxis_title="Peaje generación USD/MWh", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_agente, use_container_width=True)

        st.metric(label=f"Precio Promedio {selected_agente}", value=f"{precio_promedio_agente:.2f} US$/MWh")

    with col_right:
        st.subheader(f"Precio Promedio para Empresa: {selected_empresa}")
        df_empresa = df_filtered[df_filtered['EMPRESA'] == selected_empresa]
        df_empresa_prom = df_empresa.groupby(['FECHA', 'EMPRESA'])['Peaje generación USD/MWh'].mean().reset_index()
        precio_promedio_empresa = df_empresa['Peaje generación USD/MWh'].mean()

        fig_empresa = px.line(
            df_empresa_prom,
            x='FECHA',
            y='Peaje generación USD/MWh',
            title=f"Precio Promedio para {selected_empresa}",
            markers=True,
            line_shape='spline'
        )
        fig_empresa.update_traces(line=dict(width=3, dash='dot'), marker=dict(size=8, symbol='diamond'))
        fig_empresa.update_layout(yaxis_title="Peaje generación USD/MWh", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_empresa, use_container_width=True)

        cols_empresa = st.columns(2)
        with cols_empresa[0]:
            st.metric(label=f"Promedio {selected_empresa}", value=f"{precio_promedio_empresa:.2f} USD/MWh")

    # Evolución del Precio Promedio del Sistema
    st.subheader("Evolución del Precio Promedio del Sistema")
    df_sistema = df_filtered.groupby('FECHA')['Peaje generación USD/MWh'].mean().reset_index()
    df_sistema['Peaje generación USD/MWh'] = df_sistema['Peaje generación USD/MWh'].round(2)
    precio_promedio_sistema = df_sistema['Peaje generación USD/MWh'].mean()

    fig_sistema = px.bar(
        df_sistema,
        x='FECHA',
        y='Peaje generación USD/MWh',
        title="Evolución del Precio Promedio del Sistema",
        text_auto=True,
        color_discrete_sequence=["#b4291f"],
    )
    
    fig_sistema.update_traces(
        textposition='inside',
        textfont=dict(size=18, color='white'))

    fig_sistema.update_layout(yaxis_title="Peaje generación Promedio (USD/MWh)", xaxis_title="Fecha", showlegend=False, bargap=0.2)
    st.plotly_chart(fig_sistema, use_container_width=True)

    st.metric(label="Precio Promedio del Sistema", value=f"{precio_promedio_sistema:.2f} USD/MWh")

with tab2:
    st.header("Análisis Comparativo")
    st.subheader("Comparación de Empresas")

    df_empresas_prom_tab2 = df_filtered.groupby(['FECHA', 'EMPRESA'])['Peaje generación USD/MWh'].mean().reset_index()
    fig_comparacion = px.line(
        df_empresas_prom_tab2,
        x='FECHA',
        y='Peaje generación USD/MWh',
        color='EMPRESA',
        line_dash='EMPRESA',
        symbol='EMPRESA',
        title="Comparación de Precios Promedio por Empresa"
    )
    fig_comparacion.update_layout(
        yaxis_title="Peaje generación Promedio (USD/MWh)",
        xaxis_title="Fecha",
        legend_title="Tecnologias",
    )
    st.plotly_chart(fig_comparacion, use_container_width=True)

    st.subheader("Métricas Clave")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precio Mínimo Sistema", f"{df_filtered['Peaje generación USD/MWh'].min():.2f} USD/MWh")
    with col2:
        st.metric("Precio Promedio Sistema", f"{df_filtered['Peaje generación USD/MWh'].mean():.2f} USD/MWh")
    with col3:
        st.metric("Precio Máximo Sistema", f"{df_filtered['Peaje generación USD/MWh'].max():.2f} USD/MWh")

# Sidebar: información del sistema
st.sidebar.markdown("---")
st.sidebar.subheader("Información del Sistema")
st.sidebar.write(f"Total de agentes: {df_filtered['AGENTE'].nunique()}")
st.sidebar.write(f"Total de empresas: {df_filtered['EMPRESA'].nunique()}")
if 'FECHA' in df_filtered.columns:
    min_date = df_filtered['FECHA'].min().strftime('%Y-%m-%d')
    max_date = df_filtered['FECHA'].max().strftime('%Y-%m-%d')
    st.sidebar.write(f"Rango de fechas: {min_date} a {max_date}")