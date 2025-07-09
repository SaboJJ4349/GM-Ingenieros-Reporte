import streamlit as st
import pandas as pd
import io
from utils import safe_date_for_excel, format_date_for_display

def generate_personnel_report_excel(df_original: pd.DataFrame, df_filtrado: pd.DataFrame) -> bytes:
    """
    Genera un reporte en Excel que muestra las tareas del personal activo y
    lista al personal sin actividades según los filtros.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # --- 1. Preparar datos de personal con tareas ---
    df_exploded = df_filtrado.explode('asignados').dropna(subset=['asignados'])
    
    column_map = {
        'asignados': 'nombre',
        'proyecto': 'carpeta',
        'nombre': 'nombreTarea',
        'fecha_inicio': 'Fecha inicio',
        'fecha_limite': 'Fecha Fin'
    }
    
    report_df = df_exploded[list(column_map.keys())].rename(columns=column_map)
    
    # --- 2. Preparar lista de personal sin tareas ---
    all_personnel = set(df_original.explode('asignados')['asignados'].dropna())
    personnel_with_tasks = set(df_exploded['asignados'])
    unassigned_personnel = sorted(list(all_personnel - personnel_with_tasks))
    
    unassigned_df = pd.DataFrame(unassigned_personnel, columns=['nombre'])
    
    # --- 3. Combinar los DataFrames ---
    # Usamos concat para añadir las filas de personal sin tareas al final
    final_df = pd.concat([report_df, unassigned_df], ignore_index=True)
    
    # Rellenar NaNs con strings vacíos para evitar errores en xlsxwriter
    final_df = final_df.fillna('')
    
    # --- 4. Escribir a Excel ---
    sheet_name = 'Reporte Personal'
    final_df.to_excel(writer, index=False, sheet_name=sheet_name)
    
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Formatos
    header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F2F2F2'})
    cell_format = workbook.add_format({'border': 1})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'border': 1})

    # Aplicar formato a la cabecera
    for col_num, value in enumerate(final_df.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    # Formatear celdas y fechas
    for r_idx, row in final_df.iterrows():
        for c_idx, col_name in enumerate(final_df.columns):
            value = row[col_name]
            if col_name in ['Fecha inicio', 'Fecha Fin']:
                safe_value = safe_date_for_excel(value)
                if safe_value is not None:
                    worksheet.write_datetime(r_idx + 1, c_idx, safe_value, date_format)
                else:
                    worksheet.write(r_idx + 1, c_idx, "", cell_format)
            else:
                worksheet.write(r_idx + 1, c_idx, value, cell_format)

    # Ajustar ancho de columnas
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 40)
    worksheet.set_column('D:E', 15)

    writer.close()
    return output.getvalue()


def render_unassigned_personnel_view(df_original: pd.DataFrame, df_filtrado: pd.DataFrame):
    """
    Renderiza la vista que muestra el personal sin tareas asignadas
    según los filtros actuales y permite descargar un reporte detallado.
    """
    st.header("👤 Reporte de Personal sin Actividad")

    if df_original.empty:
        st.warning("No hay datos para analizar.")
        return

    # Lógica para mostrar en pantalla
    all_personnel = set(df_original.explode('asignados')['asignados'].dropna())
    personnel_with_tasks = set(df_filtrado.explode('asignados')['asignados'].dropna())
    unassigned_personnel = all_personnel - personnel_with_tasks

    st.write("Esta sección identifica al personal que no tiene ninguna tarea asignada que coincida con los filtros actuales.")

    if not unassigned_personnel:
        st.success("¡Todo el personal tiene tareas asignadas según los filtros actuales!")
    else:
        st.subheader("Personal sin tareas asignadas (según filtros):")
        for person in sorted(list(unassigned_personnel)):
            st.write(f"- {person}")
            
    st.markdown("---")
    
    # Botón de descarga de Excel
    st.subheader("Descargar Reporte Combinado")
    st.write("Descargue un archivo Excel que lista las tareas del personal activo y añade al final una lista del personal sin actividades.")
    excel_bytes = generate_personnel_report_excel(df_original, df_filtrado)
    
    st.download_button(
        label="📥 Descargar Reporte de Personal",
        data=excel_bytes,
        file_name='reporte_personal_actividad.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
