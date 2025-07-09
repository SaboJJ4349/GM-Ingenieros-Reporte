import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.express as px
from utils import safe_date_for_excel, format_date_for_display

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """
    Convierte un DataFrame a un archivo Excel en memoria con formato de tabla nativa
    para permitir filtros y ordenamiento, incluyendo detalles de tareas y subtareas.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # --- 1. Preparar el DataFrame para el reporte ---
    df_report = df.copy()
    
    # Añadir columna de tipo (Tarea/Subtarea)
    df_report['tipo'] = df_report['parent_id'].apply(lambda x: 'Subtarea' if pd.notna(x) else 'Tarea')
    
    # Mapeo de IDs de tareas padres a nombres
    # Se usa el mismo df filtrado para el mapeo. Si una tarea padre no está en el
    # conjunto filtrado, su nombre no aparecerá.
    parent_task_map = df.set_index('id')['nombre'].to_dict()
    df_report['tarea_padre'] = df_report['parent_id'].map(parent_task_map).fillna('')
    
    # Convertir lista de asignados a un string
    df_report['asignados'] = df_report['asignados'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # Convertir fechas NaT a None para evitar problemas en Excel
    df_report['fecha_inicio'] = df_report['fecha_inicio'].apply(safe_date_for_excel)
    df_report['fecha_limite'] = df_report['fecha_limite'].apply(safe_date_for_excel)
    
    # Mapeo de nombres de columnas a español
    column_map = {
        'proyecto': 'Carpeta',
        'estado': 'Estado',
        'nombre': 'Nombre de tarea',
        'asignados': 'Asignados',
        'fecha_inicio': 'Fecha inic.',
        'fecha_limite': 'Fecha límite',
        'prioridad': 'Prioridad',
        'tipo': 'Tipo',
        'tarea_padre': 'Tarea Padre'
    }
    
    # Seleccionar, renombrar y reordenar columnas
    df_to_write = df_report[list(column_map.keys())].rename(columns=column_map)
    final_columns_order = ['Carpeta', 'Estado', 'Tipo', 'Nombre de tarea', 'Tarea Padre', 'Asignados', 'Fecha inic.', 'Fecha límite', 'Prioridad']
    df_to_write = df_to_write[final_columns_order]

    # --- 2. Escribir la tabla de datos en Excel ---
    sheet_name = 'Reporte Detallado'
    df_to_write.to_excel(writer, index=False, sheet_name=sheet_name)
    
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Definir el rango de la tabla
    (max_row, max_col) = df_to_write.shape
    
    # Crear la tabla nativa de Excel
    worksheet.add_table(0, 0, max_row, max_col - 1, {
        'columns': [{'header': col_name} for col_name in df_to_write.columns],
        'style': 'Table Style Medium 9',
    })

    # --- 3. Ajustar formato y ancho de columnas ---
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    worksheet.set_column('G:H', 12, date_format) # Formato para columnas de fecha
    
    # Auto-ajustar ancho de las otras columnas
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 15)
    worksheet.set_column('C:C', 10)
    worksheet.set_column('D:D', 50)
    worksheet.set_column('E:E', 50)
    worksheet.set_column('F:F', 30)
    worksheet.set_column('I:I', 12)

    writer.close()
    return output.getvalue()


def render_detailed_report(df: pd.DataFrame):
    """
    Renderiza la vista del reporte detallado.
    Muestra una tabla con los datos filtrados y un botón de descarga de Excel.
    """
    st.header("📄 Reporte Detallado de Tareas")

    if df.empty:
        st.warning("No hay datos disponibles para los filtros seleccionados.")
        return

    # Preparar DataFrame para mostrar en la app
    display_df = df.copy()
    display_df['tipo'] = display_df['parent_id'].apply(lambda x: 'Subtarea' if pd.notna(x) else 'Tarea')
    
    # Mostrar tabla en la app
    st.dataframe(display_df[['nombre', 'tipo', 'estado', 'proyecto', 'asignados', 'fecha_inicio', 'fecha_limite']])

    # Botón de descarga de Excel
    excel_bytes = df_to_excel_bytes(df)
    st.download_button(
        label="📊 Descargar Reporte Detallado",
        data=excel_bytes,
        file_name='reporte_detallado_tareas.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        help="Descarga la tabla detallada de tareas y subtareas en formato Excel."
    )
