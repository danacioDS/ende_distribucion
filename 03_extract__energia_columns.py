import os
import pandas as pd

# Obtener la ruta absoluta de la carpeta donde se encuentra este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definir la carpeta "downloads" como subcarpeta de BASE_DIR
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")


def extract_columns_and_save(folder):
    """
    Extrae las columnas CENTRAL, Peaje filiales ENDE US$/MWh y PROMEDIO US$/MWh
    de cada archivo .xlsx (excluyendo archivos ya extraídos y específicos).
    """
    excluded_files = ["serie_energia_cronologica.xlsx", "serie_temporal_larga.xlsx", "ingresos_empresas_*.xlsx", 
                      "serie_ingresos_cronologica.xlsx", "serie_temporal_ingresos.xlsx", "ingresos_empresas_*.xlsx",
                      "precios_empresas_*.xlsx", "energia_empresas_*.xlsx",
                      "serie_temporal_precios.xlsx", "serie_precios_cronologica.xlsx"]

    for file in os.listdir(folder):
        if (file.endswith(".xlsx") and 
            not file.startswith("extracted_") and 
            file not in excluded_files):
            
            filepath = os.path.join(folder, file)
            try:
                # Leer el archivo Excel
                df = pd.read_excel(filepath)

                # Seleccionar columnas específicas por índice
                df = df.iloc[:, [0, 1, 6]]

                # Renombrar columnas
                df.columns = [
                    "AGENTE",
                    "Energía MWh",
                    "Potencia kW",
                ]

                # Guardar archivo con las columnas extraídas
                output_file = os.path.join(folder, f"extracted_energia_{file}")
                df.to_excel(output_file, index=False)
                print(f"✅ Archivo {file} procesado y guardado como {output_file}.")
            except Exception as e:
                print(f"❌ Error al procesar {file}: {e}")
 


if __name__ == "__main__":
    extract_columns_and_save(DOWNLOAD_FOLDER)