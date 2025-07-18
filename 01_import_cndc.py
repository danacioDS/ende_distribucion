# importador_cndc.py
import os
import requests
import zipfile
from datetime import datetime, timedelta

# Obtener la ruta absoluta de la carpeta donde se encuentra este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")

# Crear la carpeta "downloads" si no existe
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Función para generar URLs de descarga
def generate_urls(start_date, end_date):
    """Genera una lista de URLs en función del rango de fechas especificado."""
    base_url_zip = "https://www.cndc.bo/media/archivos/estadistica_mensual/c_ret_"
    base_url_xlsx = "https://www.cndc.bo/media/archivos/estadistica_mensual/c_ret_"
    urls = []
    current_date = start_date

    # Generar URLs para cada mes en el rango de fechas
    while current_date <= end_date:
        month_year = current_date.strftime("%m%y")  # Formato MMYY
        # Agregamos ambas posibles extensiones
        urls.append(f"{base_url_zip}{month_year}.zip")
        urls.append(f"{base_url_xlsx}{month_year}.xlsx")
        current_date += timedelta(days=31)
        current_date = current_date.replace(day=1)

    return urls

def download_file(url):
    """Descarga un archivo desde una URL."""
    filename = url.split("/")[-1]
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filepath, "wb") as file:
                file.write(response.content)
            print(f"Descargado: {filename}")
            return filepath
        else:
            print(f"Archivo no encontrado: {filename} (Código: {response.status_code})")
            return None
    except Exception as e:
        print(f"Error al descargar {filename}: {str(e)}")
        return None

def process_file(filepath):
    """Procesa el archivo descargado (ZIP o XLSX)."""
    if not filepath:
        return

    if filepath.endswith('.zip'):
        try:
            with zipfile.ZipFile(filepath, "r") as zip_ref:
                zip_ref.extractall(DOWNLOAD_FOLDER)
                print(f"Extraído: {os.path.basename(filepath)}")
                print("Archivos extraídos:", zip_ref.namelist())
            os.remove(filepath)
        except Exception as e:
            print(f"Error al extraer {filepath}: {str(e)}")
    elif filepath.endswith('.xlsx'):
        print(f"Archivo Excel descargado: {os.path.basename(filepath)}")
        # No necesitamos extraer nada, ya es un XLSX


if __name__ == "__main__":
    # Definir rango de fechas para la generación automática de URLs
    start_date = datetime(2023, 1, 1)
    end_date = datetime.today()

    # Generar URLs dinámicamente y procesarlas
    urls = generate_urls(start_date, end_date)
    
    for url in urls:
        filepath = download_file(url)
        if filepath:
            process_file(filepath)
