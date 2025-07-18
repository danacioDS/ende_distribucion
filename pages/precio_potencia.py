import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Configuración de la página
st.set_page_config(page_title="Dashboard de Precios de Potencia", layout="wide")
st.title("Análisis Integral de Precios de Potencia")


@st.cache_data
def load_and_transform_data():
    try:
        current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
        file_path = current_dir / "data" / "energia_con_empresas.xlsx"

        if not file_path.exists():
            st.error("Archivo no encontrado")
            return None

        df = pd.read_excel(file_path, engine="openpyxl")
        if df.empty:
            st.error("El archivo está vacío")
            return None

        df.columns = df.columns.str.strip()
        price_columns = [col for col in df.columns if "Precio Potencia US$/kW" in col]

        # Generate dynamic date mapping
        date_mapping = {}
        start_date = datetime(2023, 1, 1)
        end_date = datetime.today()
        current_date = start_date
        
        while current_date <= end_date:
            key = current_date.strftime('%m%y').lower()
            value = current_date.strftime('%Y-%m-01')
            date_mapping[key] = value
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        dfs = []
        for col in price_columns:
            period = col.split()[-1]
            temp_df = df[['AGENTE', 'EMPRESA', col]].copy()
            temp_df['FECHA'] = date_mapping.get(period, pd.NaT)  # Use NaT for unknown periods
            temp_df['Precio Potencia US$/kW'] = temp_df[col]
            temp_df['Periodo'] = period
            dfs.append(temp_df)

        transformed_df = pd.concat(dfs)
        transformed_df['FECHA'] = pd.to_datetime(transformed_df['FECHA'])
        
        # Filter out rows with NaT dates (unknown periods)
        transformed_df = transformed_df[transformed_df['FECHA'].notna()]
        
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

if 'FECHA' in df.columns:
    min_date = df['FECHA'].min()
    max_date = df['FECHA'].max()
    min_ts = datetime.timestamp(min_date)
    max_ts = datetime.timestamp(max_date)

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
    df_filtered = df

empresas = df_filtered['EMPRESA'].unique()
selected_empresa = st.sidebar.selectbox("Seleccionar Empresa", empresas)

agentes_disponibles = df_filtered[df_filtered['EMPRESA'] == selected_empresa]['AGENTE'].unique()
selected_agente = st.sidebar.selectbox("Seleccionar Agente", agentes_disponibles)

# Layout
tab1, tab2 = st.tabs(["Visión Detallada", "Visión de Promedios"])

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(f"Evolución de Precios de Potencia para Agente: {selected_agente}")
        df_agente = df_filtered[df_filtered['AGENTE'] == selected_agente]
        precio_promedio_agente = df_agente['Precio Potencia US$/kW'].mean()

        fig_agente = px.line(
            df_agente,
            x='FECHA',
            y='Precio Potencia US$/kW',
            title=f"Precios de Potencia para {selected_agente}",
            markers=True,
            line_shape='linear'
        )
        fig_agente.update_traces(line=dict(width=3), marker=dict(size=8))
        fig_agente.update_layout(yaxis_title="Precio (US$/kW)", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_agente, use_container_width=True)

        st.metric(label=f"Precio Promedio {selected_agente}", value=f"{precio_promedio_agente:.2f} US$/kW")

    with col_right:
        st.subheader(f"Precio Promedio de Potencia para Empresa: {selected_empresa}")
        df_empresa = df_filtered[df_filtered['EMPRESA'] == selected_empresa]
        df_empresa_prom = df_empresa.groupby(['FECHA', 'EMPRESA'])['Precio Potencia US$/kW'].mean().reset_index()
        precio_promedio_empresa = df_empresa['Precio Potencia US$/kW'].mean()

        if selected_empresa == "NO REGULADOS":
            df_no_regulados = df_filtered[df_filtered['EMPRESA'] == "NO REGULADOS"]
            precio_promedio_no_regulados = df_no_regulados['Precio Potencia US$/kW'].mean()

        fig_empresa = px.line(
            df_empresa_prom,
            x='FECHA',
            y='Precio Potencia US$/kW',
            title=f"Precio Promedio de Potencia para {selected_empresa}",
            markers=True,
            line_shape='spline'
        )
        fig_empresa.update_traces(line=dict(width=3, dash='dot'), marker=dict(size=8, symbol='diamond'))
        fig_empresa.update_layout(yaxis_title="Precio Promedio (US$/kW)", xaxis_title="Fecha", showlegend=False)
        st.plotly_chart(fig_empresa, use_container_width=True)

        cols_empresa = st.columns(2)
        with cols_empresa[0]:
            st.metric(label=f"Promedio {selected_empresa}", value=f"{precio_promedio_empresa:.2f} US$/kW")


    # Evolución del Precio Promedio del Sistema (una sola línea)
    st.subheader("Evolución del Precio Promedio de Potencia del Sistema")
    df_sistema = df_filtered.groupby('FECHA')['Precio Potencia US$/kW'].mean().reset_index()
    df_sistema['Precio Potencia US$/kW'] = df_sistema['Precio Potencia US$/kW'].round(2)
    precio_promedio_sistema = df_sistema['Precio Potencia US$/kW'].mean()

    fig_sistema = px.bar(
        df_sistema,
        x='FECHA',
        y='Precio Potencia US$/kW',
        title="Evolución del Precio Promedio de Potencia del Sistema",
        text_auto=True
    )
    
    fig_sistema.update_traces(
        textposition='inside',
        textfont=dict(size=18, color='white'))
    
    fig_sistema.update_layout(yaxis_title="Precio Promedio (US$/kW)", xaxis_title="Fecha", showlegend=False, bargap=0.2)
    st.plotly_chart(fig_sistema, use_container_width=True)

    st.metric(label="Precio Promedio del Sistema", value=f"{precio_promedio_sistema:.2f} US$/kW")

with tab2:
    st.header("Análisis Comparativo")
    st.subheader("Comparación de Empresas")

    df_empresas_prom_tab2 = df_filtered.groupby(['FECHA', 'EMPRESA'])['Precio Potencia US$/kW'].mean().reset_index()
    fig_comparacion = px.line(
        df_empresas_prom_tab2,
        x='FECHA',
        y='Precio Potencia US$/kW',
        color='EMPRESA',
        line_dash='EMPRESA',
        symbol='EMPRESA',
        title="Comparación de Precios Promedio de Potencia por Empresa"
    )
    fig_comparacion.update_layout(
        yaxis_title="Precio Promedio (US$/kW)",
        xaxis_title="Fecha",
        legend_title="Empresas"
    )
    st.plotly_chart(fig_comparacion, use_container_width=True)

    st.subheader("Métricas Clave")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precio Mínimo Sistema", f"{df_filtered['Precio Potencia US$/kW'].min():.2f} US$/kW")
    with col2:
        st.metric("Precio Promedio Sistema", f"{df_filtered['Precio Potencia US$/kW'].mean():.2f} US$/kW")
    with col3:
        st.metric("Precio Máximo Sistema", f"{df_filtered['Precio Potencia US$/kW'].max():.2f} US$/kW")

# Sidebar: información del sistema
st.sidebar.markdown("---")
st.sidebar.subheader("Información del Sistema")
st.sidebar.write(f"Total de agentes: {df_filtered['AGENTE'].nunique()}")
st.sidebar.write(f"Total de empresas: {df_filtered['EMPRESA'].nunique()}")
st.sidebar.write(f"Rango de fechas: {date_range[0].strftime('%Y-%m-%d')} a {date_range[1].strftime('%Y-%m-%d')}")