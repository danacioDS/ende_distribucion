import os
import pyexcel as pe

FOLDER = "downloads"

def convertir_todos_los_xls(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".xls"):
            ruta_xls = os.path.join(carpeta, archivo)
            ruta_xlsx = ruta_xls.replace('.xls', '.xlsx')

            # Saltar si el .xlsx ya existe
            if os.path.exists(ruta_xlsx):
                print(f"Ya existe: {ruta_xlsx}, saltado.")
                continue

            try:
                libro = pe.get_book(file_name=ruta_xls)
                libro.save_as(ruta_xlsx)
                print(f"Convertido exitosamente: {ruta_xlsx}")
            except Exception as e:
                print(f"Error al convertir {ruta_xls}: {e}")

# Ejecutar conversión
convertir_todos_los_xls(FOLDER)

