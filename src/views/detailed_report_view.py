import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import safe_date_for_excel, format_date_for_display

def gantt_only_to_excel(df: pd.DataFrame) -> bytes:
    """
    Genera únicamente el diagrama de Gantt en Excel usando un gráfico de barras apiladas real.
    """
    output = io.BytesIO()
    
    # Preparar el DataFrame para el Gantt
    gantt_df = df.copy()
    
    # Lógica para manejar fechas faltantes
    gantt_df.loc[gantt_df['fecha_inicio'].isnull() & gantt_df['fecha_limite'].notnull(), 'fecha_inicio'] = gantt_df['fecha_limite'] - pd.Timedelta(days=1)
    gantt_df.loc[gantt_df['fecha_limite'].isnull() & gantt_df['fecha_inicio'].notnull(), 'fecha_limite'] = gantt_df['fecha_inicio'] + pd.Timedelta(days=1)

    # Filtrar las tareas que tienen ambas fechas
    gantt_valid_df = gantt_df.dropna(subset=['fecha_inicio', 'fecha_limite']).copy()
    
    if gantt_valid_df.empty:
        # Si no hay datos válidos, crear una hoja con mensaje
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            worksheet = writer.book.add_worksheet('Sin Datos')
            worksheet.write('A1', 'No hay tareas con fechas válidas para mostrar en el diagrama de Gantt')
        return output.getvalue()
    
    # Preparar datos para el Gantt
    gantt_valid_df = gantt_valid_df.sort_values(['proyecto', 'fecha_inicio'])
    
    # Calcular fechas base
    fecha_minima = gantt_valid_df['fecha_inicio'].min()
    fecha_maxima = gantt_valid_df['fecha_limite'].max()
    
    # Convertir fechas a números de días desde la fecha mínima
    gantt_valid_df['inicio_dias'] = (gantt_valid_df['fecha_inicio'] - fecha_minima).dt.days
    gantt_valid_df['duracion'] = (gantt_valid_df['fecha_limite'] - gantt_valid_df['fecha_inicio']).dt.days + 1
    
    # Crear nombres de tareas más cortos
    gantt_valid_df['tarea_display'] = gantt_valid_df.apply(
        lambda row: f"{row['nombre'][:40]}{'...' if len(row['nombre']) > 40 else ''}", 
        axis=1
    )
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Diagrama de Gantt')
        
        # Configurar formatos
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'bg_color': '#2F5597',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        # Escribir título
        worksheet.merge_range('A1:H1', 'DIAGRAMA DE GANTT - CRONOGRAMA DE TAREAS', title_format)
        
        # Información del período
        info_format = workbook.add_format({
            'font_size': 11,
            'bg_color': '#D9E2F3',
            'border': 1,
            'align': 'center'
        })
        periodo_text = f"Período: {fecha_minima.strftime('%d/%m/%Y')} - {fecha_maxima.strftime('%d/%m/%Y')}"
        worksheet.merge_range('A2:H2', periodo_text, info_format)
        
        # Preparar datos para el gráfico
        chart_start_row = 4
        
        # Escribir headers para los datos del gráfico
        worksheet.write('A4', 'Tarea', header_format)
        worksheet.write('B4', 'Inicio (días)', header_format)
        worksheet.write('C4', 'Duración', header_format)
        worksheet.write('D4', 'Proyecto', header_format)
        
        # Escribir los datos
        for i, (_, task) in enumerate(gantt_valid_df.iterrows()):
            row = chart_start_row + 1 + i
            worksheet.write(row, 0, task['tarea_display'])
            worksheet.write(row, 1, task['inicio_dias'])
            worksheet.write(row, 2, task['duracion'])
            worksheet.write(row, 3, task['proyecto'])
        
        # Crear el gráfico de Gantt
        chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
        
        num_tasks = len(gantt_valid_df)
        
        # Agregar serie invisible para el "inicio" (para posicionar las barras)
        chart.add_series({
            'name': 'Inicio',
            'categories': [worksheet.name, chart_start_row + 1, 0, chart_start_row + num_tasks, 0],
            'values': [worksheet.name, chart_start_row + 1, 1, chart_start_row + num_tasks, 1],
            'fill': {'none': True},
            'border': {'none': True},
        })
        
        # Agregar serie visible para la "duración" (las barras del Gantt)
        chart.add_series({
            'name': 'Duración de Tareas',
            'categories': [worksheet.name, chart_start_row + 1, 0, chart_start_row + num_tasks, 0],
            'values': [worksheet.name, chart_start_row + 1, 2, chart_start_row + num_tasks, 2],
            'fill': {'color': '#4472C4'},
            'border': {'color': '#2F4F8F', 'width': 1},
        })
        
        # Configurar el gráfico
        chart.set_title({
            'name': 'Cronograma de Tareas',
            'name_font': {'size': 14, 'bold': True}
        })
        
        chart.set_x_axis({
            'name': 'Días desde el inicio del proyecto',
            'name_font': {'size': 12},
            'num_font': {'size': 10}
        })
        
        chart.set_y_axis({
            'name': 'Tareas',
            'name_font': {'size': 12},
            'reverse': True
        })
        
        chart.set_size({
            'width': 800,
            'height': max(400, num_tasks * 25)
        })
        
        chart.set_legend({'position': 'bottom'})
        
        # Insertar el gráfico en la hoja
        worksheet.insert_chart('F6', chart)
        
        # Ajustar anchos de columna
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:D', 15)
        worksheet.set_column('F:N', 12)
        
        # Crear una segunda hoja con tabla detallada
        worksheet_data = workbook.add_worksheet('Datos Detallados')
        
        # Preparar datos detallados
        detailed_data = gantt_valid_df[['tarea_display', 'proyecto', 'fecha_inicio', 'fecha_limite', 'duracion']].copy()
        detailed_data['fecha_inicio_str'] = detailed_data['fecha_inicio'].dt.strftime('%d/%m/%Y')
        detailed_data['fecha_limite_str'] = detailed_data['fecha_limite'].dt.strftime('%d/%m/%Y')
        
        # Escribir encabezados detallados
        detailed_headers = ['Tarea', 'Proyecto', 'Fecha Inicio', 'Fecha Fin', 'Duración (días)', 'Inicio (formato)', 'Fin (formato)']
        for col, header in enumerate(detailed_headers):
            worksheet_data.write(0, col, header, header_format)
        
        # Escribir datos detallados
        for i, (_, task_data) in enumerate(detailed_data.iterrows()):
            row = i + 1
            worksheet_data.write(row, 0, task_data['tarea_display'])
            worksheet_data.write(row, 1, task_data['proyecto'])
            worksheet_data.write(row, 2, task_data['fecha_inicio'])
            worksheet_data.write(row, 3, task_data['fecha_limite'])
            worksheet_data.write(row, 4, task_data['duracion'])
            worksheet_data.write(row, 5, task_data['fecha_inicio_str'])
            worksheet_data.write(row, 6, task_data['fecha_limite_str'])
        
        # Ajustar anchos en la hoja de datos
        worksheet_data.set_column('A:A', 40)
        worksheet_data.set_column('B:B', 20)
        worksheet_data.set_column('C:D', 12)
        worksheet_data.set_column('E:G', 15)
        
        # Agregar formato de fecha a las columnas de fecha
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
        worksheet_data.set_column('C:D', 12, date_format)
        
        # Añadir información de resumen
        summary_row = len(detailed_data) + 3
        summary_format = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#E6F2FF'})
        
        worksheet_data.write(summary_row, 0, 'RESUMEN:', summary_format)
        worksheet_data.write(summary_row + 1, 0, f'Total de tareas: {len(gantt_valid_df)}')
        worksheet_data.write(summary_row + 2, 0, f'Duración total del proyecto: {(fecha_maxima - fecha_minima).days + 1} días')
        worksheet_data.write(summary_row + 3, 0, f'Proyectos involucrados: {len(gantt_valid_df["proyecto"].unique())}')
    
    return output.getvalue()

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """
    Convierte un DataFrame a un archivo Excel en memoria con un diagrama de Gantt
    y formato de tabla nativa de Excel para permitir filtros y ordenamiento.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # --- 1. Preparar el DataFrame para el Gantt ---
    gantt_df = df.copy()
    
    # Lógica para manejar fechas faltantes: si solo falta una, se calcula.
    gantt_df.loc[gantt_df['fecha_inicio'].isnull() & gantt_df['fecha_limite'].notnull(), 'fecha_inicio'] = gantt_df['fecha_limite'] - pd.Timedelta(days=1)
    gantt_df.loc[gantt_df['fecha_limite'].isnull() & gantt_df['fecha_inicio'].notnull(), 'fecha_limite'] = gantt_df['fecha_inicio'] + pd.Timedelta(days=1)

    # Filtrar las tareas que tienen ambas fechas para el Gantt
    gantt_valid_df = gantt_df.dropna(subset=['fecha_inicio', 'fecha_limite']).copy()
    
    # --- 2. Nota: El diagrama de Gantt se genera por separado ---
    # Para el reporte completo, no incluimos diagrama de Gantt visual
    # El usuario puede usar el botón específico "Descargar Diagrama de Gantt" 
    # que genera un gráfico nativo de Excel mucho mejor
    
    # --- 3. Preparar el DataFrame para la tabla de datos ---
    df_report = df.copy()
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
        'prioridad': 'Prioridad'
    }
    
    # Añadir columna 'Lista' estática
    df_report['Lista'] = 'Tareas'
    
    # Seleccionar, renombrar y reordenar columnas
    df_to_write = df_report[list(column_map.keys()) + ['Lista']].rename(columns=column_map)
    final_columns_order = ['Carpeta', 'Lista', 'Estado', 'Nombre de tarea', 'Asignados', 'Fecha inic.', 'Fecha límite', 'Prioridad']
    df_to_write = df_to_write[final_columns_order]

    # --- 4. Escribir la tabla de datos en Excel ---
    sheet_name = 'Datos del Reporte'
    df_to_write.to_excel(writer, index=False, sheet_name=sheet_name)
    
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Definir el rango de la tabla
    (max_row, max_col) = df_to_write.shape
    
    # Crear la tabla nativa de Excel
    worksheet.add_table(0, 0, max_row, max_col - 1, {
        'columns': [{'header': col_name} for col_name in df_to_write.columns],
        'style': 'Table Style Medium 9', # Estilo de tabla con bandas de color
    })

    # --- 5. Ajustar formato y ancho de columnas ---
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    worksheet.set_column('F:G', 12, date_format) # Formato para columnas de fecha
    
    # Auto-ajustar ancho de las otras columnas
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:C', 15)
    worksheet.set_column('D:D', 50)
    worksheet.set_column('E:E', 30)
    worksheet.set_column('H:H', 12)

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

    # Mostrar tabla en la app
    st.dataframe(df)

    # Crear dos columnas para los botones
    col1, col2 = st.columns(2)
    
    with col1:
        # Botón de descarga de Excel con Gantt y datos
        excel_bytes = df_to_excel_bytes(df)
        st.download_button(
            label="📊 Descargar reporte completo",
            data=excel_bytes,
            file_name='reporte_datos_completo.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            help="Descarga solo la tabla de datos en Excel (sin diagrama de Gantt)"
        )
    
    with col2:
        # Botón de descarga SOLO del diagrama de Gantt optimizado
        gantt_bytes = gantt_only_to_excel(df)
        st.download_button(
            label="📈 Descargar Diagrama de Gantt",
            data=gantt_bytes,
            file_name='diagrama_gantt_optimizado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            help="Descarga únicamente el diagrama de Gantt con gráfico de barras profesional"
        )
