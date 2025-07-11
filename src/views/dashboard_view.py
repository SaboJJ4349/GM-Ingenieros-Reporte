import streamlit as st
import pandas as pd
import plotly.express as px
import io

def charts_to_excel(figs: dict) -> bytes:
    """
    Convierte un diccionario de figuras de Plotly en un archivo Excel,
    insertando cada gráfico como una imagen.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Gráficos del Dashboard')
        
        # Formato para los títulos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#DDEBF7',
            'font_color': 'black',
            'border': 1
        })
        
        row_offset = 1
        for title, fig in figs.items():
            # Usar un tema claro para la exportación para evitar fondos negros
            fig.layout.template = "plotly_white"

            # Cambiar colores para la exportación
            if title == "Tareas por Prioridad":
                new_colors = px.colors.qualitative.Pastel
                for i, trace in enumerate(fig.data):
                    if hasattr(trace, 'marker'):
                        trace.marker.color = new_colors[i % len(new_colors)]

            image_data = io.BytesIO(fig.to_image(format="png", scale=2))
            worksheet.write(f'A{row_offset}', title, header_format)
            worksheet.insert_image(f'A{row_offset + 1}', title, {'image_data': image_data})
            row_offset += 30

    output.seek(0)
    return output.getvalue()

def render_dashboard(df: pd.DataFrame):
    """
    Renderiza la vista del dashboard ejecutivo con KPIs y gráficos.
    """
    st.header("📊 Dashboard Ejecutivo")

    if df.empty:
        st.warning("No hay datos disponibles para los filtros seleccionados.")
        return

    # --- KPIs ---
    total_tareas = len(df)
    tareas_pendientes = len(df[df['estado'] == 'pendiente'])
    tareas_en_progreso = len(df[df['estado'] == 'en progreso'])
    tareas_completadas = len(df[df['estado'] == 'completado'])
    tareas_aprobadas = len(df[df['estado'] == 'aprobado'])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tareas", total_tareas)
    col2.metric("Pendientes", tareas_pendientes)
    col3.metric("En Progreso", tareas_en_progreso)
    col4.metric("Completadas", tareas_completadas)
    col5.metric("Aprobados", tareas_aprobadas)
    

    st.markdown("---")

    # --- Gráficos ---
    figs_to_export = {}
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribución por Estado")
        estado_counts = df['estado'].value_counts()
        fig_pie = px.pie(
            values=estado_counts.values, 
            names=estado_counts.index, 
            title="Tareas por Estado"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        figs_to_export["Tareas por Estado"] = fig_pie

    with col2:
        st.subheader("Distribución de Tareas por Prioridad")
        
        # Traducción de los valores de prioridad
        priority_translation = {
            'normal': 'Normal',
            'high': 'Alta',
            'low': 'Baja',
            'urgent': 'Urgente'
        }
        
        # Copia para evitar SettingWithCopyWarning
        df_copy = df.copy()
        df_copy['prioridad_traducida'] = df_copy['prioridad'].map(priority_translation)
        
        prioridad_counts = df_copy['prioridad_traducida'].value_counts().reset_index()
        prioridad_counts.columns = ['Prioridad', 'Número de Tareas']
        
        fig_bar = px.bar(
            prioridad_counts,
            x='Prioridad', 
            y='Número de Tareas',
            title="Tareas por Prioridad",
            labels={'x': 'Prioridad', 'y': 'Número de Tareas'},
            color='Prioridad',
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        figs_to_export["Tareas por Prioridad"] = fig_bar

    # --- Botón de Descarga ---
    st.markdown("---")
    
    excel_data = charts_to_excel(figs_to_export)
    
    st.download_button(
        label="📥 Descargar Gráficos en Excel",
        data=excel_data,
        file_name="dashboard_graficos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
