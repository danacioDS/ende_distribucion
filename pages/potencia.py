import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

# Configuración de la página
st.set_page_config(page_title="Dashboard de Potencia", layout="wide")
st.title("Análisis Integral de Potencia")

# 1. Optimización de carga de datos
@st.cache_data
def load_and_transform_data():
    try:
        # Ruta optimizada usando Path
        current_dir = Path(__file__).parent
        file_path = current_dir.parent / "data" / "serie_energia.xlsx"
        
        # Validación de ruta
        if not file_path.exists():
            st.error(f"Archivo no encontrado: {file_path}")
            return None
            
        # Leer solo columnas necesarias
        df = pd.read_excel(file_path, engine="openpyxl", 
                          usecols=lambda x: "Potencia kW" in x or x in ['AGENTE', 'EMPRESA'])
        
        if df.empty:
            st.error("El archivo está vacío")
            return None

        # 2. Transformación vectorizada
        df.columns = df.columns.str.strip()
        energy_cols = [col for col in df.columns if "Potencia kW" in col]
        
        # Crear mapeo de fechas optimizado
        date_mapping = {}
        current_date = datetime(2023, 1, 1)
        while current_date <= datetime(2025, 12, 1):
            key = current_date.strftime('%m%Y')
            date_mapping[key] = current_date.strftime('%Y-%m-01')
            current_date = current_date.replace(month=current_date.month + 1) if current_date.month < 12 else current_date.replace(year=current_date.year + 1, month=1)

        # Transformación con melt
        melted = df.melt(
            id_vars=['AGENTE', 'EMPRESA'],
            value_vars=energy_cols,
            var_name='Periodo',
            value_name='Potencia kW'
        )
        
        # Extraer periodo y mapear fecha
        melted['Periodo'] = melted['Periodo'].str.split().str[-1]
        melted['FECHA'] = melted['Periodo'].apply(
            lambda x: date_mapping.get(x[:2] + x[2:], pd.NaT)
        )
        
        # Filtrar y convertir fechas
        melted = melted[melted['FECHA'].notna()]
        melted['FECHA'] = pd.to_datetime(melted['FECHA'])
        
        return melted

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

# Cargar datos
df = load_and_transform_data()
if df is None:
    st.stop()

# 3. Filtros optimizados
st.sidebar.title("Filtros y Configuración")

# Manejo de fechas
if not df.empty:
    min_date = df['FECHA'].min().to_pydatetime()
    max_date = df['FECHA'].max().to_pydatetime()
    
    selected_range = st.sidebar.slider(
        "Rango de fechas",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM"
    )
    
    # Filtrar DataFrame
    mask = (df['FECHA'] >= pd.Timestamp(selected_range[0])) & (df['FECHA'] <= pd.Timestamp(selected_range[1]))
    df_filtered = df[mask].copy()
else:
    df_filtered = df
    st.warning("No hay datos disponibles para filtrar")

# 4. Pre-cálculos globales
total_potencia_sistema = df_filtered['Potencia kW'].sum()
empresas = df_filtered['EMPRESA'].unique().tolist()

# Selección de empresa
selected_empresa = st.sidebar.selectbox("Seleccionar Empresa", empresas)
agentes_disponibles = df_filtered[df_filtered['EMPRESA'] == selected_empresa]['AGENTE'].unique().tolist()
selected_agente = st.sidebar.selectbox("Seleccionar Agente", agentes_disponibles)

# Layout principal
tab1, tab2 = st.tabs(["Visión Detallada", "Visión de Promedios"])

# 5. Funciones para gráficos
def plot_agent_energy(df_agente, agent_name):
    """Crea gráfico de evolución para un agente"""
    if df_agente.empty:
        return None
    
    fig = px.line(
        df_agente,
        x='FECHA',
        y='Potencia kW',
        title=f"Potencia para {agent_name}",
        markers=True
    )
    fig.update_traces(
        line=dict(width=3, color="#06a161"),
        marker=dict(size=8, symbol='circle', color='#06a161')
    )
    fig.update_layout(
        yaxis_title="Potencia (kW)", 
        xaxis_title="Fecha", 
        showlegend=False,
        template='plotly_white'
    )
    return fig

def plot_company_energy(df_empresa, company_name):
    """Crea gráfico de evolución para una empresa"""
    if df_empresa.empty:
        return None
    
    # Agrupar por fecha
    df_grouped = df_empresa.groupby('FECHA', as_index=False)['Potencia kW'].sum()

    fig = px.line(
        df_grouped,
        x='FECHA',
        y='Potencia kW',
        title=f"Potencia para {company_name}",
        markers=True
    )
    fig.update_traces(
        line=dict(width=3, color='#d62728'),
        marker=dict(size=8, symbol='diamond', color='#d62728')
    )
    fig.update_layout(
        yaxis_title="Potencia (kW)", 
        xaxis_title="Fecha", 
        showlegend=False,
        template='plotly_white'
    )
    return fig

# 6. Contenido para pestañas
with tab1:
    col_left, col_right = st.columns(2)
    
    # Columna izquierda - Agente
    with col_left:
        st.subheader(f"Evolución del Agente: {selected_agente}")
        df_agente = df_filtered[df_filtered['AGENTE'] == selected_agente]
        
        if not df_agente.empty:
            # Gráfico
            fig_agente = plot_agent_energy(df_agente, selected_agente)
            st.plotly_chart(fig_agente, use_container_width=True)
            
            # Métricas optimizadas
            potencia_total_agente = df_agente['Potencia kW'].sum()
            potencia_promedio_agente = df_agente['Potencia kW'].mean()
            porcentaje_agente = (potencia_total_agente / total_potencia_sistema) * 100

            col1, col2 = st.columns(2)
            col1.metric("Potencia Promedio", f"{potencia_promedio_agente:,.2f} kW")
            col2.metric("Participación", f"{porcentaje_agente:.2f}%")
        else:
            st.warning(f"No hay datos para: {selected_agente}")
    
    # Columna derecha - Empresa
    with col_right:
        st.subheader(f"Evolución de la Empresa: {selected_empresa}")
        df_empresa = df_filtered[df_filtered['EMPRESA'] == selected_empresa]
        
        if not df_empresa.empty:
            # Gráfico
            fig_empresa = plot_company_energy(df_empresa, selected_empresa)
            st.plotly_chart(fig_empresa, use_container_width=True)
            
            # Métricas optimizadas
            potencia_total_empresa = df_empresa['Potencia kW'].sum()
            potencia_promedio_empresa = df_empresa.groupby('FECHA')['Potencia kW'].sum().mean()
            porcentaje_empresa = (potencia_total_empresa / total_potencia_sistema) * 100

            col1, col2 = st.columns(2)
            col1.metric("Potencia Promedio", f"{potencia_promedio_empresa:,.2f} kW")
            col2.metric("Participación", f"{porcentaje_empresa:.2f}%")
        else:
            st.warning(f"No hay datos para: {selected_empresa}")
    
    # Gráfico del sistema - ÁREA HORIZONTAL MANTENIDA
    st.subheader("Evolución del Sistema")



    # Evolución del sistema
    if not df_filtered.empty:
        st.subheader("Evolución de la Potencia Móvil del Sistema")
        df_sistema = df_filtered.groupby('FECHA')['Potencia kW'].sum().reset_index()
        df_sistema['Potencia kW'] = df_sistema['Potencia kW'].round(2)
        potencia_promedio_sistema = df_sistema['Potencia kW'].mean()

        fig_sistema = px.bar(
            df_sistema,
            x='FECHA',
            y='Potencia kW',
            color='Potencia kW',  # blues Mapea valores a colores
            color_continuous_scale='Cividis',  # Escala de colores
            title="Evolución de la Potencia Móvil del Sistema",
            text_auto=True
        )
        
        fig_sistema.update_traces(
            textposition='inside',
            textfont=dict(size=16, color='white'))
        
        fig_sistema.update_layout(
            yaxis_title="Potencia kW", 
            xaxis_title="Fecha", 
            showlegend=False, 
            bargap=0.2
        )
        st.plotly_chart(fig_sistema, use_container_width=True)

        st.metric(label="Potencia Promedio del Sistema", value=f"{potencia_promedio_sistema:,.2f} kW")
    else:
        st.warning("No hay datos disponibles para mostrar la evolución del sistema")
    
    
    # Participación por empresa (barras horizontales)
    st.subheader("Participación por Empresa")
    if not df_filtered.empty:
        # Cálculo optimizado
        participacion = (
            df_filtered.groupby('EMPRESA', as_index=False)['Potencia kW']
            .sum()
            .assign(Porcentaje=lambda x: (x['Potencia kW'] / total_potencia_sistema) * 100)
            .sort_values('Porcentaje', ascending=False)
        )
        
        fig_bar = px.bar(
            participacion,
            x='Porcentaje',
            y='EMPRESA',
            orientation='h',
            color='Porcentaje',
            color_continuous_scale='Reds',
            text='Porcentaje',
            labels={'Porcentaje': 'Participación (%)', 'EMPRESA': ''}
        )
        
        fig_bar.update_traces(
            texttemplate='%{x:.2f}%',
            textposition='outside',
            marker_line=dict(color='#000', width=0.5)
        )
        
        fig_bar.update_layout(
            height=600,
            xaxis_range=[0, participacion['Porcentaje'].max() * 1.15],
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Datos insuficientes para participación")

# 7. Pestaña de comparación con PARTICIPACIÓN PROMEDIO
with tab2:
    st.header("Análisis Comparativo")
    
    if not df_filtered.empty:
        # Gráfico comparativo de empresas
        st.subheader("Comparación entre Empresas")
        
        # Agrupación eficiente
        df_comparacion = (
            df_filtered.groupby(['FECHA', 'EMPRESA'], as_index=False)
            ['Potencia kW'].sum()
        )
        
        fig_comparativo = px.line(
            df_comparacion,
            x='FECHA',
            y='Potencia kW',
            color='EMPRESA',
            markers=True,
            line_shape='spline',
            title="Comparación de Potencia por Empresa"
        )
        
        fig_comparativo.update_layout(
            yaxis_title="Potencia (kW)",
            xaxis_title="Fecha",
            legend_title="Empresas",
            height=500
        )
        st.plotly_chart(fig_comparativo, use_container_width=True)
        
        # Tabla de resumen
        st.subheader("Resumen de Potencia por Empresa")
        st.subheader("Resumen Estadístico")

        # Calcular total del sistema por fecha
        total_por_mes = df_filtered.groupby('FECHA', as_index=False, sort=False)['Potencia kW'].sum()
        total_por_mes = total_por_mes.rename(columns={'Potencia kW': 'Total_Sistema'})

        # Calcular potencia por empresa por fecha
        empresa_por_mes = df_filtered.groupby(['FECHA', 'EMPRESA'], as_index=False)['Potencia kW'].sum()

        # Combinar y calcular participación mensual
        df_participacion = pd.merge(empresa_por_mes, total_por_mes, on='FECHA')
        df_participacion['Participacion'] = (df_participacion['Potencia kW'] / df_participacion['Total_Sistema']) * 100

        # Calcular estadísticas (manteniendo valores numéricos)
        stats = (
            df_participacion.groupby('EMPRESA', as_index=False)
            .agg(
                Minimo=('Potencia kW', 'min'),
                Promedio=('Potencia kW', 'mean'),
                Maximo=('Potencia kW', 'max'),
                Participacion_Promedio=('Participacion', 'mean')
            )
        )

        # ORDENAR por participación promedio DESCENDENTE (usando columna numérica)
        stats = stats.sort_values(by='Participacion_Promedio', ascending=False)

        # Renombrar columnas
        stats = stats.rename(columns={
            'EMPRESA': 'Empresa',
            'Minimo': 'Mínimo (MWh)',
            'Promedio': 'Promedio (MWh)',
            'Maximo': 'Máximo (MWh)',
            'Participacion_Promedio': 'Participación Promedio (%)'
        })

        # Formatear valores (después del ordenamiento)
        stats['Mínimo (MWh)'] = stats['Mínimo (MWh)'].apply(lambda x: f"{x:,.2f}")
        stats['Promedio (MWh)'] = stats['Promedio (MWh)'].apply(lambda x: f"{x:,.2f}")
        stats['Máximo (MWh)'] = stats['Máximo (MWh)'].apply(lambda x: f"{x:,.2f}")
        stats['Participación Promedio (%)'] = stats['Participación Promedio (%)'].apply(lambda x: f"{x:.2f}%")

# Mostrar tabla ordenada
st.dataframe(stats)

# 8. Panel informativo optimizado
st.sidebar.markdown("---")
st.sidebar.subheader("Métricas del Sistema")
if not df_filtered.empty:
    st.sidebar.metric("Agentes", df_filtered['AGENTE'].nunique())
    st.sidebar.metric("Empresas", df_filtered['EMPRESA'].nunique())
    st.sidebar.metric("Potencia Total", f"{total_potencia_sistema:,.2f} kW")
    st.sidebar.caption(f"Periodo: {df_filtered['FECHA'].min().strftime('%Y-%m')} a {df_filtered['FECHA'].max().strftime('%Y-%m')}")
else:
    st.sidebar.warning("Sin datos para mostrar métricas")