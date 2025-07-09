import os

# ---------------------------------------------------
# Configuración para que Kaleido encuentre el binario
# ---------------------------------------------------
# Intentamos rutas comunes; la primera que exista la usamos.
for candidate in (
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome-stable",
):
    if os.path.exists(candidate):
        os.environ["BROWSER_PATH"] = candidate
        break
else:
    # Si no se encuentra ningún binario, emitimos un warning
    print("⚠️ WARNING: No se detectó Chrome/Chromium. Verifica packages.txt")

# (Opcional) Habilitar logs de debug de Kaleido
# os.environ["KALEIDO_DEBUG"] = "1"

import streamlit as st
import pandas as pd
from data_loader import load_and_normalize_json
from processors import DataManager

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

    # --- Session State para filtros ---
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
    if 'gantt_selected_proyectos' not in st.session_state:
        st.session_state.gantt_selected_proyectos = data_manager_original.get_unique_values('proyecto')

    # --- Barra lateral de filtros ---
    st.sidebar.header("Filtros Globales")
    areas = data_manager_original.get_unique_values('area')
    st.session_state.selected_areas = st.sidebar.multiselect(
        "Filtrar por Área", areas, key='multiselect_areas',
        default=st.session_state.selected_areas
    )
    proyectos_filtrados = data_manager_original.filter_by_area(
        st.session_state.selected_areas
    ).get_unique_values('proyecto')
    st.session_state.selected_proyectos = st.sidebar.multiselect(
        "Filtrar por Proyecto", proyectos_filtrados, key='multiselect_proyectos',
        default=st.session_state.selected_proyectos
    )
    estados = data_manager_original.get_unique_values('estado')
    st.session_state.selected_estados = st.sidebar.multiselect(
        "Filtrar por Estado", estados, key='multiselect_estados',
        default=st.session_state.selected_estados
    )
    min_date, max_date = st.session_state.date_range
    sel_start, sel_end = st.sidebar.date_input(
        "Filtrar por Fecha de Inicio",
        value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
    )
    st.session_state.date_range = (sel_start, sel_end)

    # Aplicar filtros
    filtered_manager = (
        data_manager_original
        .filter_by_area(st.session_state.selected_areas)
        .filter_by_project(st.session_state.selected_proyectos)
        .filter_by_status(st.session_state.selected_estados)
        .filter_by_date_range(
            pd.to_datetime(sel_start),
            pd.to_datetime(sel_end)
        )
    )
    df_filtrado = filtered_manager.get_data()
    st.info(f"Mostrando {len(df_filtrado)} de {len(df_original)} tareas según filtros.")

    # --- Pestañas ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard Ejecutivo",
        "📄 Reporte Detallado",
        "📈 Diagrama de Gantt",
        "👤 Personal sin Tareas",
        "⭐ Reporte General"
    ])
    with tab1:
        render_dashboard(df_filtrado)
    with tab2:
        render_detailed_report(df_filtrado)
    with tab3:
        render_gantt_view(df_original)
    with tab4:
        render_unassigned_personnel_view(df_original, df_filtrado)
    with tab5:
        render_general_activity_report(df_filtrado)

if __name__ == "__main__":
    main()
