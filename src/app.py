import json
from datetime import datetime
import pandas as pd
import streamlit as st

# ---------------------------------------------
# Función para cargar y aplanar el JSON de tareas
# ---------------------------------------------
def load_and_flatten_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    tasks = []
    subtasks = []

    def parse_date(d):
        try:
            return datetime.strptime(d, "%d/%m/%y").date() if d else None
        except:
            return None

    for area, proyectos in raw.items():
        for proyecto, contenido in proyectos.items():
            for carpeta, estados in contenido.items():
                # carpeta es la 'carpeta' principal dentro de cada proyecto
                for subcarpeta, lista in estados.items():
                    # subcarpeta equivale al estado (pendiente, en progreso, etc.)
                    for t in lista:
                        tasks.append({
                            'area': area,
                            'proyecto': proyecto,
                            'carpeta': carpeta,
                            'estado': subcarpeta,
                            'id': t.get('id'),
                            'nombre': t.get('nombre'),
                            'asignados': t.get('asignados', []),
                            'fecha_inicio': parse_date(t.get('fecha_inicio')),
                            'fecha_limite': parse_date(t.get('fecha_limite')),
                            'prioridad': t.get('prioridad')
                        })
                        for sub in t.get('subtareas', []):
                            subtasks.append({
                                'parent_id': t.get('id'),
                                'nombre': sub.get('nombre'),
                                'estado': sub.get('estado'),
                                'asignados': sub.get('asignados', []),
                                'fecha_inicio': parse_date(sub.get('fecha_inicio')),
                                'fecha_limite': parse_date(sub.get('fecha_limite')),
                                'prioridad': sub.get('prioridad')
                            })

    df_tasks = pd.DataFrame(tasks)
    df_subtasks = pd.DataFrame(subtasks)
    return df_tasks, df_subtasks

# ---------------------------------------------
# Aplicación Streamlit
# ---------------------------------------------
def main():
    st.set_page_config(page_title="📋 Tareas y Subtareas", layout="wide")
    st.title("📋 Tareas y Subtareas con Filtros de Carpeta y Subcarpeta")

    # Cargar y aplanar JSON
    df_tasks, df_subtasks = load_and_flatten_json('datos.json')
    if df_tasks.empty:
        st.error("No se pudieron cargar las tareas.")
        return

    # Sidebar: filtros globales
    st.sidebar.header("Filtros")

    # 1. Filtro por área
    areas = sorted(df_tasks['area'].unique())
    selected_areas = st.sidebar.multiselect("Área", areas, default=areas)

    # 2. Filtro por proyecto
    proyectos = sorted(
        df_tasks[df_tasks['area'].isin(selected_areas)]['proyecto'].unique()
    )
    selected_proyectos = st.sidebar.multiselect("Proyecto", proyectos, default=proyectos)

    # 3. Filtro por carpeta (nivel intermedio dentro de cada proyecto)
    carpetas = sorted(
        df_tasks[
            df_tasks['area'].isin(selected_areas) &
            df_tasks['proyecto'].isin(selected_proyectos)
        ]['carpeta'].unique()
    )
    selected_carpetas = st.sidebar.multiselect("Carpeta", carpetas, default=carpetas)

    # 4. Filtro por subcarpeta (estado)
    subcarpetas = sorted(
        df_tasks[df_tasks['carpeta'].isin(selected_carpetas)]['estado'].unique()
    )
    selected_subcarpetas = st.sidebar.multiselect(
        "Subcarpeta (Estado)", subcarpetas, default=subcarpetas
    )

    # 5. Filtro por rango de fecha de inicio
    min_fecha = df_tasks['fecha_inicio'].min()
    max_fecha = df_tasks['fecha_inicio'].max()
    selected_range = st.sidebar.date_input(
        "Rango Fecha de Inicio",
        value=(min_fecha, max_fecha),
        min_value=min_fecha,
        max_value=max_fecha
    )

    # Aplicar filtros encadenados
    df_filtered = df_tasks[
        df_tasks['area'].isin(selected_areas) &
        df_tasks['proyecto'].isin(selected_proyectos) &
        df_tasks['carpeta'].isin(selected_carpetas) &
        df_tasks['estado'].isin(selected_subcarpetas) &
        df_tasks['fecha_inicio'].between(selected_range[0], selected_range[1])
    ]

    st.info(f"Mostrando {len(df_filtered)} tareas de {len(df_tasks)} totales.")

    # Mostrar tareas y sus subtareas dentro de expanders
    for _, tarea in df_filtered.iterrows():
        with st.expander(f"{tarea['id']} - {tarea['nombre']} ({tarea['carpeta']} / {tarea['estado']})"):
            st.markdown(f"**Prioridad:** {tarea['prioridad'] or '-'}")
            st.markdown(f"**Asignados:** {', '.join(tarea['asignados']) or '-'}")
            st.markdown(f"**Fecha inicio:** {tarea['fecha_inicio'] or '-'}")
            st.markdown(f"**Fecha límite:** {tarea['fecha_limite'] or '-'}")

            subs = df_subtasks[df_subtasks['parent_id'] == tarea['id']]
            if not subs.empty:
                st.table(subs[['nombre','estado','prioridad','fecha_inicio','fecha_limite','asignados']])
            else:
                st.write("_Sin subtareas_")

if __name__ == '__main__':
    main()
