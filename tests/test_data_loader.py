import pytest
import pandas as pd
import json
import os
import sys

# Añadir el directorio raíz del proyecto al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_loader import load_and_normalize_json

@pytest.fixture
def sample_json_data():
    return {
        "Area1": {
            "Proyecto1": {
                "Tareas": {
                    "pendiente": [
                        {
                            "id": "t1",
                            "nombre": "Tarea 1",
                            "estado": "pendiente",
                            "asignados": ["User A"],
                            "fecha_inicio": "01/01/25",
                            "fecha_limite": "02/01/25",
                            "prioridad": "normal",
                            "subtareas": [
                                {
                                    "nombre": "Subtarea 1.1",
                                    "estado": "pendiente",
                                    "asignados": [],
                                    "fecha_inicio": None,
                                    "fecha_limite": None,
                                    "prioridad": None
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }

@pytest.fixture
def temp_json_file(tmp_path, sample_json_data):
    file_path = tmp_path / "test_data.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sample_json_data, f)
    return str(file_path)

def test_load_and_normalize_json(temp_json_file):
    # Ejecutar la función
    df = load_and_normalize_json(temp_json_file)

    # 1. Verificar que el DataFrame no está vacío y tiene el número correcto de filas (1 tarea + 1 subtarea)
    assert not df.empty
    assert len(df) == 2

    # 2. Verificar que las columnas de contexto se añadieron correctamente
    assert 'area' in df.columns
    assert 'proyecto' in df.columns
    assert df['area'].iloc[0] == "Area1"
    assert df['proyecto'].iloc[0] == "Proyecto1"

    # 3. Verificar el aplanamiento de subtareas
    tarea_principal = df[df['id'] == 't1']
    subtarea = df[df['parent_id'] == 't1']
    
    assert len(tarea_principal) == 1
    assert tarea_principal['parent_id'].iloc[0] is None
    
    assert len(subtarea) == 1
    assert subtarea['nombre'].iloc[0] == "Subtarea 1.1"
    assert subtarea['parent_id'].iloc[0] == 't1'

    # 4. Verificar la conversión de fechas
    assert pd.api.types.is_datetime64_any_dtype(df['fecha_inicio'])
    assert pd.api.types.is_datetime64_any_dtype(df['fecha_limite'])
    assert pd.isna(subtarea['fecha_inicio'].iloc[0]) # Verificar que maneja NaT correctamente

    # 5. Verificar que 'asignados' es una lista
    assert isinstance(df['asignados'].iloc[0], list)
    assert isinstance(df['asignados'].iloc[1], list)
