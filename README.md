# Ende Distri Project

## Overview
The Ende Distri project is a Python application designed to download and process files from specified URLs. It automates the retrieval of statistical data from the CNDC website, handling both ZIP and XLSX file formats.

## Project Structure
```
ende_distri
├── 01_import_cndc.py      # Main logic for downloading and processing files
├── requirements.txt        # Python dependencies
├── Dockerfile              # Instructions for building the Docker image
└── README.md               # Project documentation
```

## Requirements
This project requires the following Python libraries:
- `requests`: For making HTTP requests.
- `zipfile`: For handling ZIP file extraction.
- `datetime`: For date manipulation.

## Docker Setup

### Building the Docker Image
To build the Docker image for this application, navigate to the project directory and run the following command:
```
docker build -t ende_distri .
```

### Running the Docker Container
After building the image, you can run the application using:
```
docker run --rm ende_distri
```

## Usage
The application will automatically generate URLs based on the specified date range, download the files, and process them accordingly. Ensure that you have an active internet connection when running the application.

## Contributing
Contributions to the Ende Distri project are welcome. Please feel free to submit issues or pull requests for any enhancements or bug fixes.

### Como Construir y correr el contenedor ###

# Desde la misma carpeta del Dockerfile
docker build -t ende_distri .

# Ejecutar contenedor
docker run --rm -p 8501:8501 ende_distri
