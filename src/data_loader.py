import pandas as pd
import json
from typing import List, Dict, Any

def parse_and_correct_date(date_str):
    """
    Parsea una cadena de fecha DD/MM/YY y maneja explícitamente los años de dos dígitos
    para asegurar que se interpreten como fechas del siglo XXI.
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return pd.NaT
    try:
        # Dividir la fecha para manejar el año manualmente
        parts = date_str.split('/')
        if len(parts) != 3:
            return pd.NaT
        
        day, month, year_str = parts
        year = int(year_str)
        
        # Corregir años de dos dígitos (ej: 25 -> 2025)
        if year < 100:
            year += 2000

        # Reconstruir la fecha con el año corregido y convertirla
        return pd.to_datetime(f"{day}/{month}/{year}", format='%d/%m/%Y')

    except (ValueError, TypeError):
        return pd.NaT

def load_and_normalize_json(file_path: str) -> pd.DataFrame:
    """
    Carga un archivo JSON, procesa su estructura anidada de tareas y subtareas,
    y lo convierte en un DataFrame de Pandas, preservando la relación jerárquica.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_tasks = []
    
    for area, proyectos in data.items():
        for proyecto, detalles_proyecto in proyectos.items():
            if detalles_proyecto and isinstance(detalles_proyecto, dict):
                task_container = next(iter(detalles_proyecto.values()), None)
                if task_container and isinstance(task_container, dict):
                    for estado, tareas in task_container.items():
                        for tarea in tareas:
                            # Procesar la tarea principal
                            processed_task = tarea.copy()
                            processed_task['area'] = area
                            processed_task['proyecto'] = proyecto
                            processed_task['parent_id'] = None
                            processed_task['is_subtask'] = False
                            
                            subtasks = processed_task.pop('subtareas', [])
                            all_tasks.append(processed_task)

                            # Procesar las subtareas asociadas
                            for i, subtask in enumerate(subtasks):
                                processed_subtask = subtask.copy()
                                processed_subtask['area'] = area
                                processed_subtask['proyecto'] = proyecto
                                processed_subtask['parent_id'] = tarea.get('id')
                                # Generar un ID único y estable para la subtarea
                                processed_subtask['id'] = f"sub_{tarea.get('id')}_{i}"
                                processed_subtask['is_subtask'] = True
                                all_tasks.append(processed_subtask)

    if not all_tasks:
        return pd.DataFrame()

    df = pd.DataFrame(all_tasks)

    # Limpieza y estandarización de datos usando la nueva función robusta
    date_columns = ['fecha_inicio', 'fecha_limite']
    for col in date_columns:
        df[col] = df[col].apply(parse_and_correct_date)

    df['asignados'] = df['asignados'].apply(lambda x: x if isinstance(x, list) else [])

    return df
