import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import os  # Importar módulo os para manejar rutas

# Configuración de la página
st.set_page_config(page_title="Dashboard de Energía", layout="wide")
st.title("Análisis Integral de Energía")

@st.cache_data
def load_and_transform_data():
    try:
        # Obtener la ruta absoluta del directorio actual del script
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        # Subir un nivel al directorio padre y luego entrar a 'data'
        base_path = current_dir.parent / "data"
        file_path = base_path / "serie_energia.xlsx"
        
        st.info(f"Buscando archivo en: {file_path}")
        
        # Verificar si la ruta base existe
        if not base_path.exists():
            st.error(f"Directorio no encontrado: {base_path}")
            # Mostrar archivos disponibles para diagnóstico
            available_files = "\n".join([f.name for f in current_dir.parent.glob('*')])
            st.error(f"Archivos disponibles en el directorio padre:\n{available_files}")
            return None

        # Verificar si el archivo existe
        if not file_path.exists():
            st.error(f"Archivo no encontrado: {file_path}")
            # Mostrar archivos en el directorio data
            if base_path.exists():
                available_files = "\n".join([f.name for f in base_path.glob('*')])
                st.error(f"Archivos disponibles en {base_path}:\n{available_files}")
            return None

        df = pd.read_excel(file_path, engine="openpyxl")
        
        if df.empty:
            st.error("El archivo está vacío")
            return None

        # ============================================================
        # INICIO DEL CÓDIGO DE TRANSFORMACIÓN (copiado de la versión original)
        # ============================================================
        df.columns = df.columns.str.strip()
        price_columns = [col for col in df.columns if "Energía MWh" in col]

        # Generar mapeo dinámico de fechas
        date_mapping = {}
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2025, 12, 1)
        current_date = start_date
        
        while current_date <= end_date:
            key = current_date.strftime('%m%Y')
            value = current_date.strftime('%Y-%m-01')
            date_mapping[key] = value
            
            # Mover al siguiente mes
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        dfs = []
        for col in price_columns:
            period = col.split()[-1]
            temp_df = df[['AGENTE', 'EMPRESA', col]].copy()
            
            # Usar el formato MMYYYY (ej: 012023)
            formatted_period = period[:2] + period[2:]  # Aseguramos formato 012023
            
            temp_df['FECHA'] = date_mapping.get(formatted_period, pd.NaT)
            temp_df['Energía MWh'] = temp_df[col]
            temp_df['Periodo'] = period
            dfs.append(temp_df)

        transformed_df = pd.concat(dfs)
        transformed_df['FECHA'] = pd.to_datetime(transformed_df['FECHA'])
        
        # Filtrar filas con fechas desconocidas
        transformed_df = transformed_df[transformed_df['FECHA'].notna()]
        # ============================================================
        # FIN DEL CÓDIGO DE TRANSFORMACIÓN
        # ============================================================
        
        return transformed_df

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Cargar datos
df = load_and_transform_data()
if df is None:
    st.stop()

# Sidebar para filtros
st.sidebar.title("Filtros y Configuración")

# CORRECCIÓN CLAVE: Manejo adecuado de fechas para el slider
if 'FECHA' in df.columns and not df.empty:
    # Convertir a objetos datetime de Python
    min_date = df['FECHA'].min().to_pydatetime()
    max_date = df['FECHA'].max().to_pydatetime()
    
    # Asegurarse de que las fechas sean válidas
    if min_date and max_date:
        selected_range = st.sidebar.slider(
            "Seleccionar rango de fechas",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM"
        )
        
        # Convertir los valores seleccionados a Timestamp para comparación
        start_date = pd.Timestamp(selected_range[0])
        end_date = pd.Timestamp(selected_range[1])
        
        df_filtered = df[
            (df['FECHA'] >= start_date) & 
            (df['FECHA'] <= end_date)
        ]
    else:
        df_filtered = df
        st.warning("Fechas no válidas. Mostrando todos los datos.")
else:
    df_filtered = df
    st.warning("No se encontraron datos de fecha válidos. Mostrando todos los datos.")

# Resto del código sin cambios...
empresas = df_filtered['EMPRESA'].unique().tolist()
selected_empresa = st.sidebar.selectbox("Seleccionar Empresa", empresas)

agentes_disponibles = df_filtered[df_filtered['EMPRESA'] == selected_empresa]['AGENTE'].unique().tolist()
selected_agente = st.sidebar.selectbox("Seleccionar Agente", agentes_disponibles)

# Layout principal
tab1, tab2 = st.tabs(["Visión Detallada", "Visión de Promedios"])

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        if selected_agente:
            st.subheader(f"Evolución de la Energía para Agente: {selected_agente}")
            df_agente = df_filtered[df_filtered['AGENTE'] == selected_agente]
            
            if not df_agente.empty:
                energia_promedio_agente = df_agente['Energía MWh'].median()

                fig_agente = px.line(
                    df_agente,
                    x='FECHA',
                    y='Energía MWh',
                    title=f"Energía para {selected_agente}",
                    markers=True,
                    line_shape='linear'
                )
                fig_agente.update_traces(line=dict(width=3), marker=dict(size=14, symbol='circle'))
                fig_agente.update_layout(yaxis_title="Energía (MWh)", xaxis_title="Fecha", showlegend=False)
                st.plotly_chart(fig_agente, use_container_width=True)

                st.metric(label=f"Energía Promedio {selected_agente}", value=f"{energia_promedio_agente:,.2f} MWh")
            else:
                st.warning(f"No hay datos disponibles para el agente: {selected_agente}")

    with col_right:
        if selected_empresa:
            st.subheader(f"Energía Promedio para Empresa: {selected_empresa}")
            df_empresa = df_filtered[df_filtered['EMPRESA'] == selected_empresa]
            
            if not df_empresa.empty:
                df_empresa_prom = df_empresa.groupby(['FECHA', 'EMPRESA'])['Energía MWh'].sum().reset_index()
                # energia_promedio_empresa = df_empresa['Energía MWh'].mean()
                energia_promedio_empresa = df_empresa_prom['Energía MWh'].mean()

                fig_empresa = px.line(
                    df_empresa_prom,
                    x='FECHA',
                    y='Energía MWh',
                    title=f"Energía Promedio para {selected_empresa}",
                    markers=True,
                    line_shape='spline'
                )
                
                fig_empresa.update_traces(
                    line=dict(color='#FF0000'),  # Color de la línea
                    marker=dict(color='#FF0000')  # Color de los marcadores
                    )
                

                fig_empresa.update_traces(line=dict(width=3, dash='dot'), marker=dict(size=8, symbol='diamond'))
                fig_empresa.update_layout(yaxis_title="Energía Promedio (MWh)", xaxis_title="Fecha", showlegend=False)
                st.plotly_chart(fig_empresa, use_container_width=True)

                st.metric(label=f"Promedio {selected_empresa}", value=f"{energia_promedio_empresa:,.2f} MWh")
            else:
                st.warning(f"No hay datos disponibles para la empresa: {selected_empresa}")

    # Evolución del sistema
    if not df_filtered.empty:
        st.subheader("Evolución de la Energía Promedio del Sistema")
        df_sistema = df_filtered.groupby('FECHA')['Energía MWh'].sum().reset_index()
        df_sistema['Energía MWh'] = df_sistema['Energía MWh'].round(2)
        energia_promedio_sistema = df_sistema['Energía MWh'].mean()

        fig_sistema = px.bar(
            df_sistema,
            x='FECHA',
            y='Energía MWh',
            color='Energía MWh',  # Mapea valores a colores
            color_continuous_scale='Viridis',  # Escala de colores
            title="Evolución de la Energía Promedio del Sistema",
            text_auto=True
        )
        
        fig_sistema.update_traces(
            textposition='inside',
            textfont=dict(size=12, color='white'))
        
        fig_sistema.update_layout(
            yaxis_title="Energía MWh", 
            xaxis_title="Fecha", 
            showlegend=False, 
            bargap=0.2
        )
        st.plotly_chart(fig_sistema, use_container_width=True)

        st.metric(label="Energía Promedio del Sistema", value=f"{energia_promedio_sistema:,.2f} MWh")
    else:
        st.warning("No hay datos disponibles para mostrar la evolución del sistema")

# Análisis comparativo de empresas
with tab2:
    if not df_filtered.empty:
        st.header("Análisis Comparativo")
        st.subheader("Comparación de Empresas")

        df_empresas_prom_tab2 = df_filtered.groupby(['FECHA', 'EMPRESA'])['Energía MWh'].sum().reset_index()
 

        fig_comparacion = px.line(
            df_empresas_prom_tab2,
            x='FECHA',
            y='Energía MWh',
            color='EMPRESA',
            markers=True, # Marcadores para puntos de datos
            line_shape='spline',  # Curva suave
            symbol='EMPRESA', # Símbolos para cada empresa
            title="Comparación de Energía Promedio por Empresa",
            height=800,
            width=1000
        )


        fig_comparacion.update_layout(
            yaxis_title="Energía Promedio (MWh)",
            xaxis_title="Fecha",
            legend_title="Empresas"
        )
        st.plotly_chart(fig_comparacion, use_container_width=True)

        # Métricas clave
        st.subheader("Métricas Clave")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Energía Mínima Sistema", f"{df_filtered.groupby('FECHA')['Energía MWh'].sum().min():,.2f} MWh")
        with col2:
            st.metric("Energía Promedio Sistema", f"{df_filtered.groupby('FECHA')['Energía MWh'].sum().mean():,.2f} MWh")
        with col3:
            st.metric("Energía Máxima Sistema", f"{df_filtered.groupby('FECHA')['Energía MWh'].sum().max():,.2f} MWh")
    else:
        st.warning("No hay datos disponibles para análisis comparativo")

# Sidebar: información del sistema
st.sidebar.markdown("---")
st.sidebar.subheader("Información del Sistema")
if 'FECHA' in df_filtered.columns and not df_filtered.empty:
    min_fecha = df_filtered['FECHA'].min().strftime('%Y-%m-%d')
    max_fecha = df_filtered['FECHA'].max().strftime('%Y-%m-%d')
    st.sidebar.write(f"Total de agentes: {df_filtered['AGENTE'].nunique()}")
    st.sidebar.write(f"Total de empresas: {df_filtered['EMPRESA'].nunique()}")
    st.sidebar.write(f"Rango de fechas: {min_fecha} a {max_fecha}")
else:
    st.sidebar.warning("Datos insuficientes para mostrar información del sistema")