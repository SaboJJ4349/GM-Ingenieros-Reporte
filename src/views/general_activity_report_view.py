import streamlit as st
import pandas as pd
import io
from utils import safe_date_for_excel, format_date_for_display

def generate_general_report_excel(df: pd.DataFrame) -> bytes:
    """
    Genera un reporte complejo en Excel agrupado por persona, incluyendo tablas y gráficos.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    workbook = writer.book
    worksheet = workbook.add_worksheet('Reporte General')

    # --- Formatos ---
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'valign': 'vcenter'})
    cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    bold_format = workbook.add_format({'bold': True, 'border': 1})

    # --- Lógica del Reporte ---
    df_exploded = df.explode('asignados').dropna(subset=['asignados'])
    if df_exploded.empty:
        worksheet.write(0, 0, "No hay datos para los filtros seleccionados.")
        writer.close()
        return output.getvalue()

    assignees = df_exploded['asignados'].unique()
    
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 50)
    worksheet.set_column('C:E', 15)
    worksheet.set_column('G:H', 15)
    worksheet.set_column('J:J', 35)


    current_row = 0
    worksheet.write(current_row, 0, "Reporte de General Actividades", title_format)
    current_row += 2

    for assignee in assignees:
        person_df = df_exploded[df_exploded['asignados'] == assignee].copy()
        
        # --- 1. Tabla de Tareas por Persona ---
        task_headers = ["Nombre", "Tarea", "fecha inicio", "fecha fin", "estado"]
        for col_num, header in enumerate(task_headers):
            worksheet.write(current_row, col_num, header, header_format)
        current_row += 1

        for _, task in person_df.iterrows():
            worksheet.write(current_row, 0, assignee, cell_format)
            worksheet.write(current_row, 1, task['nombre'], cell_format)
            worksheet.write(current_row, 2, format_date_for_display(task['fecha_inicio']), cell_format)
            worksheet.write(current_row, 3, format_date_for_display(task['fecha_limite']), cell_format)
            worksheet.write(current_row, 4, task['estado'], cell_format)
            current_row += 1
        
        summary_start_row = current_row + 1

        # --- 2. Tabla de Resumen de Estado ---
        status_summary = person_df['estado'].value_counts().reindex(['pendiente', 'progreso', 'completado'], fill_value=0)
        worksheet.write(summary_start_row, 0, "EstadoTarea", bold_format)
        worksheet.write(summary_start_row, 1, "Total de tareas", bold_format)
        
        summary_data_row = summary_start_row + 1
        for status, count in status_summary.items():
            worksheet.write(summary_data_row, 0, status, cell_format)
            worksheet.write(summary_data_row, 1, count, cell_format)
            summary_data_row += 1

        # --- 3. Gráfico de Torta ---
        chart = workbook.add_chart({'type': 'pie'})
        chart.set_title({'name': 'Total de tareas segun estado'})
        
        # [sheetname, first_row, first_col, last_row, last_col]
        chart.add_series({
            'name':       'Total de tareas',
            'categories': ['Reporte General', summary_start_row + 1, 0, summary_start_row + len(status_summary), 0],
            'values':     ['Reporte General', summary_start_row + 1, 1, summary_start_row + len(status_summary), 1],
            'points': [
                {'fill': {'color': '#4F81BD'}}, # Azul para pendiente
                {'fill': {'color': '#C0504D'}}, # Rojo para progreso
                {'fill': {'color': '#9BBB59'}}, # Verde para completado
            ],
        })
        
        worksheet.insert_chart(summary_start_row, 3, chart, {'x_offset': 25, 'y_offset': 10})

        current_row = summary_data_row + 5 # Dejar espacio para el siguiente reporte

    writer.close()
    return output.getvalue()

def render_general_activity_report(df: pd.DataFrame):
    """
    Renderiza la vista que permite descargar el reporte general de actividades.
    """
    st.header("⭐ Reporte General de Actividades por Persona")
    st.write("Este reporte genera un archivo Excel detallado, agrupado por persona, con tablas de tareas, resúmenes de estado y gráficos, basado en los filtros actuales.")
    
    if df.empty:
        st.warning("No hay datos disponibles para generar el reporte con los filtros seleccionados.")
        return

    excel_bytes = generate_general_report_excel(df)
    
    st.download_button(
        label="📥 Descargar Reporte General como Excel",
        data=excel_bytes,
        file_name='reporte_general_actividades.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
