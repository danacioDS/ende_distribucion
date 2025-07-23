# Imagen base con Python 3.10
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar utilidades del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto al contenedor
COPY . .

# Expone el puerto por si usas Streamlit
EXPOSE 8501

# Comando por defecto para ejecutar un script central que orqueste los demás
CMD ["python", "run_all.py"]
