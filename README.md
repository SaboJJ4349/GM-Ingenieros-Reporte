# Dashboard de Reportes y Productividad

Una aplicación Streamlit para visualizar y generar reportes de productividad con diagramas de Gantt nativos en Excel.

## Características

- **Dashboard interactivo** con métricas clave
- **Reporte detallado** con datos filtrados y descarga en Excel
- **Diagrama de Gantt** nativo en Excel (no imágenes)
- **Análisis de personal no asignado**
- **Reporte de actividades generales**

## Instalación Local

1. Clonar el repositorio
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la aplicación:
   ```bash
   streamlit run src/app.py
   ```

## Despliegue en Streamlit Cloud

1. Subir el proyecto a GitHub
2. Conectar el repositorio en [share.streamlit.io](https://share.streamlit.io)
3. Configurar la aplicación:
   - **Main file path**: `src/app.py`
   - **Python version**: 3.11+

## Estructura del Proyecto

```
├── src/
│   ├── app.py                 # Punto de entrada principal
│   ├── data_loader.py         # Carga y normalización de datos
│   ├── processors.py          # Procesamiento de datos
│   ├── utils.py              # Utilidades generales
│   └── views/                # Vistas de la aplicación
│       ├── dashboard_view.py
│       ├── detailed_report_view.py
│       ├── gantt_view.py
│       ├── unassigned_personnel_view.py
│       └── general_activity_report_view.py
├── datos.json                # Archivo de datos
├── requirements.txt          # Dependencias
└── .streamlit/
    └── config.toml          # Configuración de Streamlit
```

## Funcionalidades de Descarga

- **Reporte Completo**: Tabla de datos filtrada en Excel
- **Diagrama de Gantt**: Gráfico de barras apiladas nativo en Excel con formato profesional

## Tecnologías Utilizadas

- Streamlit
- Pandas
- Plotly
- XlsxWriter
- Python 3.11+
