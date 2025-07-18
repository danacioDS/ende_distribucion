import streamlit as st

# Configuración general de la página
st.set_page_config(
    page_title="Dashboard Energía Bolivia",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Dashboard Energético de Bolivia")

# Imagen representativa
st.image(
    "https://media.istockphoto.com/id/1032683612/photo/solar-energy-and-wind-power-stations.jpg?s=612x612&w=0&k=20&c=KXElDTxrRrXG72sVD4QGnctJU1iSMroKPOl6XUfGHNk=",
    caption="Energías renovables impulsando el futuro de Bolivia"
)


# Texto introductorio
st.markdown("""
## 🔍 Exploración de Indicadores del Sector Eléctrico

Este dashboard interactivo te permite analizar los principales indicadores tarifarios y económicos del sector eléctrico boliviano, con enfoque especial en:

- 🌞 **Precio de Energía**
- 💡 **Precio de Potencia**
- 📊 **Precio Monómico**

Está diseñado para apoyar la toma de decisiones estratégicas en torno a la transición energética, la planificación regulatoria y el análisis de desempeño de los agentes del sistema eléctrico.

---

🧭 **Usa el menú lateral izquierdo** para navegar por las secciones del dashboard.
""")

st.success("📌 Este dashboard es parte del esfuerzo por promover la transparencia y sostenibilidad del sistema eléctrico nacional.")


