import streamlit as st
import pandas as pd
import plotly.express as px
import io
from utils import safe_date_for_excel

def gantt_only_to_excel(df: pd.DataFrame, original_df: pd.DataFrame) -> bytes:
    """
    Genera únicamente el diagrama de Gantt en Excel usando un gráfico de barras apiladas real.
    """
    import xlsxwriter
    
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
        lambda row: f"  - {row['nombre']}" if pd.notna(row['parent_id']) else row['nombre'],
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
        parent_task_map = original_df.set_index('id')['nombre'].to_dict()
        detailed_data = gantt_valid_df[['nombre', 'proyecto', 'fecha_inicio', 'fecha_limite', 'duracion', 'parent_id']].copy()
        detailed_data['tipo'] = detailed_data['parent_id'].apply(lambda x: 'Subtarea' if pd.notna(x) else 'Tarea')
        
        # Escribir encabezados detallados
        detailed_headers = ['Tarea/Subtarea', 'Proyecto', 'Tipo', 'Fecha Inicio', 'Fecha Fin', 'Duración (días)', 'Tarea Padre']
        for col, header in enumerate(detailed_headers):
            worksheet_data.write(0, col, header, header_format)
        
        # Escribir datos detallados
        for i, (_, task_data) in enumerate(detailed_data.iterrows()):
            row = i + 1
            worksheet_data.write(row, 0, task_data['nombre'])
            worksheet_data.write(row, 1, task_data['proyecto'])
            worksheet_data.write(row, 2, task_data['tipo'])
            worksheet_data.write(row, 3, task_data['fecha_inicio'])
            worksheet_data.write(row, 4, task_data['fecha_limite'])
            worksheet_data.write(row, 5, task_data['duracion'])
            parent_name = parent_task_map.get(task_data['parent_id'], '')
            worksheet_data.write(row, 6, parent_name)
        
        # Ajustar anchos en la hoja de datos
        worksheet_data.set_column('A:A', 40)
        worksheet_data.set_column('B:B', 20)
        worksheet_data.set_column('C:C', 10)
        worksheet_data.set_column('D:E', 12)
        worksheet_data.set_column('F:G', 15)
        
        # Agregar formato de fecha a las columnas de fecha
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
        worksheet_data.set_column('D:E', 12, date_format)
        
        # Añadir información de resumen
        summary_row = len(detailed_data) + 3
        summary_format = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#E6F2FF'})
        
        worksheet_data.write(summary_row, 0, 'RESUMEN:', summary_format)
        worksheet_data.write(summary_row + 1, 0, f'Total de tareas: {len(gantt_valid_df)}')
        worksheet_data.write(summary_row + 2, 0, f'Duración total del proyecto: {(fecha_maxima - fecha_minima).days + 1} días')
        worksheet_data.write(summary_row + 3, 0, f'Proyectos involucrados: {len(gantt_valid_df["proyecto"].unique())}')
    
    return output.getvalue()

def render_gantt_view(df: pd.DataFrame):
    """
    Renderiza la vista del diagrama de Gantt con un selector de proyectos dedicado.
    """
    st.header("📈 Diagrama de Gantt")

    # Selector de proyectos para el Gantt que usa su propio estado de sesión
    all_projects = sorted(df['proyecto'].unique())
    if 'gantt_selected_proyectos' not in st.session_state:
        st.session_state.gantt_selected_proyectos = all_projects
    
    st.session_state.gantt_selected_proyectos = st.multiselect(
        "Selecciona los proyectos a visualizar en el Gantt",
        options=all_projects,
        default=st.session_state.gantt_selected_proyectos
    )

    if not st.session_state.gantt_selected_proyectos:
        st.warning("Por favor, selecciona al menos un proyecto para visualizar el Gantt.")
        return

    # Filtrar el DataFrame por los proyectos seleccionados en el estado de sesión del Gantt
    gantt_df = df[df['proyecto'].isin(st.session_state.gantt_selected_proyectos)].copy()

    # --- Filtro de Subtareas ---
    if 'gantt_include_subtasks' not in st.session_state:
        st.session_state.gantt_include_subtasks = True

    st.session_state.gantt_include_subtasks = st.checkbox(
        "Incluir subtareas en el gráfico",
        value=st.session_state.gantt_include_subtasks,
        help="Marca esta casilla para mostrar las subtareas. Desmárcala para ver solo las tareas principales."
    )

    if not st.session_state.gantt_include_subtasks:
        gantt_df = gantt_df[gantt_df['parent_id'].isnull()]

    # Lógica para manejar fechas faltantes: si solo falta una, se calcula.
    gantt_df.loc[gantt_df['fecha_inicio'].isnull() & gantt_df['fecha_limite'].notnull(), 'fecha_inicio'] = gantt_df['fecha_limite'] - pd.Timedelta(days=1)
    gantt_df.loc[gantt_df['fecha_limite'].isnull() & gantt_df['fecha_inicio'].notnull(), 'fecha_limite'] = gantt_df['fecha_inicio'] + pd.Timedelta(days=1)
    
    # Filtrar las tareas que aún no tienen ambas fechas
    gantt_df = gantt_df.dropna(subset=['fecha_inicio', 'fecha_limite'])

    if gantt_df.empty:
        st.warning("Los proyectos seleccionados no tienen tareas con fechas de inicio y fin definidas o derivables.")
        return

    gantt_df['tipo'] = gantt_df['parent_id'].apply(lambda x: 'Subtarea' if pd.notna(x) else 'Tarea')
    
    if st.session_state.gantt_include_subtasks:
        gantt_df['task_label'] = gantt_df.apply(
            lambda row: f"  - {row['nombre']}" if pd.notna(row['parent_id']) else f"{row['proyecto']} - {row['nombre']}",
            axis=1
        )
    else:
        gantt_df['task_label'] = gantt_df.apply(lambda row: f"{row['proyecto']} - {row['nombre']}", axis=1)

    # Usar una altura dinámica para el gráfico
    chart_height = max(600, len(gantt_df) * 25)

    # Usar una paleta de colores más vibrante y pasar las fechas como objetos datetime
    fig = px.timeline(
        gantt_df,
        x_start="fecha_inicio",
        x_end="fecha_limite",
        y="task_label",
        color="tipo",
        title="Cronograma de Tareas por Proyecto",
        labels={"task_label": "Tarea", "tipo": "Tipo"},
        color_discrete_map={
            'Tarea': '#1f77b4',
            'Subtarea': '#ff7f0e'
        },
        height=chart_height
    )

    # Dejar que Plotly maneje el formato del eje X automáticamente para la exportación
    min_date = gantt_df['fecha_inicio'].min()
    max_date = gantt_df['fecha_limite'].max()
    fig.update_xaxes(range=[min_date, max_date])
    
    fig.update_yaxes(autorange="reversed")
    
    st.plotly_chart(fig, use_container_width=True)

    # Informar al usuario sobre los proyectos que no se pueden mostrar
    original_projects = df['proyecto'].unique()
    gantt_projects = gantt_df['proyecto'].unique()
    excluded_projects = set(original_projects) - set(gantt_projects)

    if excluded_projects:
        st.info(f"Nota: Los siguientes proyectos no se muestran en el Gantt porque sus tareas filtradas no tienen fechas de inicio y fin definidas: {', '.join(sorted(list(excluded_projects)))}")

    # --- Botón de Descarga ---
    st.markdown("---")
    
    excel_data = gantt_only_to_excel(gantt_df, df)
    
    st.download_button(
        label="📈 Descargar Diagrama de Gantt",
        data=excel_data,
        file_name="diagrama_gantt_optimizado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Descarga el diagrama de Gantt con gráfico nativo de Excel"
    )
