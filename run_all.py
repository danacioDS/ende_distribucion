import subprocess

# Ejecutar scripts .py
scripts = [
    "01_import_cndc.py",
    "02_convert.py",
    "03_extract_energia_columns.py",
    "03_extract_ingresos_columns.py",
    "03_extract_precios_columns.py"
]

for script in scripts:
    print(f"Ejecutando {script}...")
    subprocess.run(["python", script], check=True)

# Ejecutar notebooks (requiere jupyter en requirements.txt)
notebooks = [
    "04_notebook_energia.ipynb",
    "04_notebook_ingresos.ipynb",
    "04_notebook_precios.ipynb"
]

for notebook in notebooks:
    print(f"Ejecutando notebook {notebook}...")
    subprocess.run([
        "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", notebook
    ], check=True)

# Ejecutar script final (ejemplo)
final_script = "05_final.py"
print(f"Ejecutando script final: {final_script}...")
subprocess.run(["python", final_script], check=True)