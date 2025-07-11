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
GM-Ingenieros-Reporte-main/
├── .devcontainer/
│   └── devcontainer.json
├── .streamlit/
│   └── config.toml                   # renombrado desde config_app.toml
├── data/
│   ├── raw/
│   │   └── datos_clickup.json        # antes Json/datos.json
│   └── processed/
│       └── report.json               # antes datos.json en la raíz
├── scripts/
│   └── clickup_to_json.py            # antes Json/main.py
├── src/
│   ├── app.py                        # entrypoint Streamlit
│   ├── data_loader.py
│   ├── processors.py
│   ├── utils.py
│   └── views/
│       ├── dashboard.py              # renombrado desde dashboard_view.py
│       ├── detailed_report.py        # renombrado desde detailed_report_view*.py
│       ├── gantt.py                  # renombrado desde gantt_view.py
│       ├── unassigned_personnel.py   # renombrado desde unassigned_personnel_view.py
│       └── general_activity.py       # renombrado desde general_activity_report_view.py
├── tests/
│   └── test_data_loader.py           # ejemplo de prueba
├── requirements.txt
├── README.md
└── .gitignore
```

## Funcionalidades de Descarga

- **Reporte Completo**: Tabla de datos filtrada en Excel
- **Diagrama de Gantt**: Gráfico de barras apiladas nativo en Excel con formato profesional

## Tecnologías Utilizadas

- Streamlit
- Pandas
- Plotly
- XlsxWriter
- Python 3.13+
