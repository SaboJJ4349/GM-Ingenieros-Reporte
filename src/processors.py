import pandas as pd
from typing import List, Optional

class DataManager:
    """
    Clase para gestionar la lógica de negocio y el procesamiento de datos de tareas.
    Se inicializa con un DataFrame y proporciona métodos para filtrarlo.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def filter_by_date_range(self, start_date: Optional[pd.Timestamp], end_date: Optional[pd.Timestamp]) -> 'DataManager':
        """
        Filtra el DataFrame para incluir solo tareas dentro del rango de fechas especificado.
        Se aplica sobre la columna 'fecha_inicio'.
        """
        temp_df = self.df
        if pd.notna(start_date):
            temp_df = temp_df[temp_df['fecha_inicio'] >= start_date]
        if pd.notna(end_date):
            temp_df = temp_df[temp_df['fecha_inicio'] <= end_date]
        return DataManager(temp_df)

    def filter_by_status(self, statuses: Optional[List[str]]) -> 'DataManager':
        """Filtra el DataFrame por una lista de estados."""
        if statuses:
            return DataManager(self.df[self.df['estado'].isin(statuses)])
        return self

    def filter_by_area(self, areas: Optional[List[str]]) -> 'DataManager':
        """Filtra el DataFrame por una lista de áreas."""
        if areas:
            return DataManager(self.df[self.df['area'].isin(areas)])
        return self

    def filter_by_project(self, projects: Optional[List[str]]) -> 'DataManager':
        """Filtra el DataFrame por una lista de proyectos."""
        if projects:
            return DataManager(self.df[self.df['proyecto'].isin(projects)])
        return self

    def get_data(self) -> pd.DataFrame:
        """Devuelve el DataFrame filtrado actual."""
        return self.df

    def get_unique_values(self, column: str) -> List[str]:
        """
        Devuelve una lista de valores únicos para una columna dada,
        excluyendo los valores nulos o vacíos.
        """
        return sorted(self.df[column].dropna().unique().tolist())
