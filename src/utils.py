import pandas as pd
from typing import Any

def safe_date_for_excel(date_value: Any) -> Any:
    """
    Convierte una fecha de pandas a un formato seguro para Excel.
    Si la fecha es NaT (Not a Time) o None, retorna None.
    Si es una fecha válida, la retorna como está.
    """
    if pd.isna(date_value) or date_value is None:
        return None
    return date_value

def format_date_for_display(date_value: Any) -> str:
    """
    Formatea una fecha para mostrar en Excel como string.
    Si la fecha es NaT o None, retorna string vacío.
    """
    if pd.isna(date_value) or date_value is None:
        return ""
    try:
        return date_value.strftime('%d/%m/%Y')
    except (AttributeError, ValueError):
        return ""