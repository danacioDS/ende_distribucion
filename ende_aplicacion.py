import os
import streamlit as st
from PIL import Image

# Título principal con emoji
st.title("⚡ Bienvenido a la App de Energía Renovable 🌱")

# Diseño con dos columnas
col1, col2 = st.columns([2, 1])

# Columna izquierda: Texto de bienvenida
with col1:
    st.header("🌍 Transición Energética y Sostenibilidad")
    st.write(
        "Esta aplicación proporciona análisis sobre energía renovable, "
        "infraestructura de recarga y costos energéticos en Bolivia. "
        "Utiliza el menú de la izquierda para explorar cada sección."
    )
    st.write(
        "Esta app utiliza información proveniente del Comité Nacional de Despacho de Carga (CNDC)"
    )

# Columna derecha: Imagen adicional de energías renovables
with col2:
    st.image(
        "https://i0.wp.com/energysavingpros.com/wp-content/uploads/2016/11/"
        "EnergySavingPros_SunPower.jpg?resize=2048%2C1160&ssl=1",
        use_container_width=True
    )
    st.caption("Energías renovables: Solar, Eólica e Hidroeléctrica")

# Menú de navegación en la barra lateral
st.sidebar.title("🔍 Menú de Navegación")
st.sidebar.write("Selecciona una sección para explorar datos y análisis.")

# Mensaje motivacional
st.success("💡¡Explora la transición energética y descubre insights clave!🚀")









