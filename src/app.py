import streamlit as st
import pandas as pd
from data_loader import load_and_normalize_json
from processors import DataManager

# Importar las funciones de renderizado de las vistas
from views.dashboard_view import render_dashboard
from views.detailed_report_view import render_detailed_report
from views.gantt_view import render_gantt_view
from views.unassigned_personnel_view import render_unassigned_personnel_view
from views.general_activity_report_view import render_general_activity_report

def main():
    st.set_page_config(
        page_title="Dashboard de Reportes",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Dashboard de Reportes y Productividad")

    # Cargar datos
    df_original = load_and_normalize_json('datos.json')

    if df_original.empty:
        st.error("No se pudieron cargar los datos o el archivo está vacío.")
        return

    data_manager_original = DataManager(df_original)

    # --- Inicializar Session State para filtros ---
    if 'selected_areas' not in st.session_state:
        st.session_state.selected_areas = data_manager_original.get_unique_values('area')
    if 'selected_proyectos' not in st.session_state:
        st.session_state.selected_proyectos = data_manager_original.get_unique_values('proyecto')
    if 'selected_estados' not in st.session_state:
        st.session_state.selected_estados = data_manager_original.get_unique_values('estado')
    if 'date_range' not in st.session_state:
        min_date = df_original['fecha_inicio'].min()
        max_date = df_original['fecha_inicio'].max()
        st.session_state.date_range = (min_date, max_date)
    # Inicializar un estado independiente para los proyectos del Gantt
    if 'gantt_selected_proyectos' not in st.session_state:
        st.session_state.gantt_selected_proyectos = data_manager_original.get_unique_values('proyecto')


    # --- Barra lateral de filtros ---
    st.sidebar.header("Filtros Globales")
    
    # Filtro de Área (controla el de proyecto)
    areas = data_manager_original.get_unique_values('area')
    st.session_state.selected_areas = st.sidebar.multiselect(
        "Filtrar por Área", areas, key='multiselect_areas', default=st.session_state.selected_areas
    )

    # Filtro de Proyecto (dinámico)
    proyectos_filtrados_por_area = data_manager_original.filter_by_area(st.session_state.selected_areas).get_unique_values('proyecto')
    st.session_state.selected_proyectos = st.sidebar.multiselect(
        "Filtrar por Proyecto", proyectos_filtrados_por_area, key='multiselect_proyectos', default=st.session_state.selected_proyectos
    )

    # Filtro de Estado
    estados = data_manager_original.get_unique_values('estado')
    st.session_state.selected_estados = st.sidebar.multiselect(
        "Filtrar por Estado", estados, key='multiselect_estados', default=st.session_state.selected_estados
    )

    # Filtro de Rango de Fechas
    min_date, max_date = st.session_state.date_range
    selected_start_date, selected_end_date = st.sidebar.date_input(
        "Filtrar por Fecha de Inicio",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    st.session_state.date_range = (selected_start_date, selected_end_date)


    # Aplicar filtros
    filtered_manager = (data_manager_original
                        .filter_by_area(st.session_state.selected_areas)
                        .filter_by_project(st.session_state.selected_proyectos)
                        .filter_by_status(st.session_state.selected_estados)
                        .filter_by_date_range(pd.to_datetime(st.session_state.date_range[0]), pd.to_datetime(st.session_state.date_range[1])))

    df_filtrado = filtered_manager.get_data()

    st.info(f"Mostrando {len(df_filtrado)} de {len(df_original)} tareas según los filtros seleccionados.")
    
    # --- Navegación por Pestañas ---
    tab_names = [
        "📊 Dashboard Ejecutivo", 
        "📄 Reporte Detallado", 
        "📈 Diagrama de Gantt", 
        "👤 Personal sin Tareas",
        "⭐ Reporte General"
    ]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)

    with tab1:
        render_dashboard(df_filtrado)

    with tab2:
        render_detailed_report(df_filtrado)

    with tab3:
        # La vista de Gantt ahora usa el DataFrame original y su propio estado de sesión
        render_gantt_view(df_original)
    
    with tab4:
        render_unassigned_personnel_view(df_original, df_filtrado)

    with tab5:
        render_general_activity_report(df_filtrado)


if __name__ == "__main__":
    main()
