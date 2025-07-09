import requests
import json
from datetime import datetime

# === CONFIGURACIÓN ===
API_TOKEN = "(ESRCIBE TU TOKEN )"
ESPACIO_ID = "eL CODIGO iD "  # Espacio "Administración y Sistemas"

HEADERS = {
    "Authorization": API_TOKEN
}

def formatear_fecha(fecha_ms):
    if fecha_ms:
        try:
            dt = datetime.fromtimestamp(int(fecha_ms) / 1000)
            return dt.strftime("%d/%m/%y")
        except:
            return None
    return None

def obtener_carpetas(space_id):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    r = requests.get(url, headers=HEADERS)
    return r.json()["folders"] if r.ok else []

def obtener_listas(folder_id):
    url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
    r = requests.get(url, headers=HEADERS)
    return r.json()["lists"] if r.ok else []

def obtener_tareas(list_id):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task?subtasks=true&include_closed=true"
    r = requests.get(url, headers=HEADERS)
    return r.json()["tasks"] if r.ok else []

# === PROCESO PRINCIPAL ===

estructura = { "Administración y Sistemas": {} }

carpetas = obtener_carpetas(ESPACIO_ID)

for carpeta in carpetas:
    nombre_carpeta = carpeta["name"]
    estructura["Administración y Sistemas"][nombre_carpeta] = {}

    listas = obtener_listas(carpeta["id"])

    for lista in listas:
        nombre_lista = lista["name"]
        lista_id = lista["id"]
        estructura["Administración y Sistemas"][nombre_carpeta][nombre_lista] = {}

        tareas = obtener_tareas(lista_id)

        # Agrupar subtareas por ID de padre
        subtareas_dict = {}
        for tarea in tareas:
            if tarea.get("parent"):
                parent_id = tarea["parent"]
                if parent_id not in subtareas_dict:
                    subtareas_dict[parent_id] = []
                subtareas_dict[parent_id].append({
                    "nombre": tarea.get("name"),
                    "estado": tarea["status"]["status"].lower() if tarea.get("status") else "sin estado",
                    "asignados": [a["username"] for a in tarea.get("assignees", [])],
                    "fecha_inicio": formatear_fecha(tarea.get("start_date")),
                    "fecha_limite": formatear_fecha(tarea.get("due_date")),
                    "prioridad": tarea["priority"]["priority"] if tarea.get("priority") else None
                })

        for tarea in tareas:
            if tarea.get("parent"): continue  # Ya fue capturada como subtarea

            estado = tarea["status"]["status"].lower() if tarea.get("status") else "sin estado"

            tarea_info = {
                "id": tarea.get("id"),
                "nombre": tarea.get("name"),
                "estado": estado,
                "asignados": [a["username"] for a in tarea.get("assignees", [])],
                "fecha_inicio": formatear_fecha(tarea.get("start_date")),
                "fecha_limite": formatear_fecha(tarea.get("due_date")),
                "prioridad": tarea["priority"]["priority"] if tarea.get("priority") else None,
                "subtareas": subtareas_dict.get(tarea.get("id"), [])
            }

            if estado not in estructura["Administración y Sistemas"][nombre_carpeta][nombre_lista]:
                estructura["Administración y Sistemas"][nombre_carpeta][nombre_lista][estado] = []

            estructura["Administración y Sistemas"][nombre_carpeta][nombre_lista][estado].append(tarea_info)

# === GUARDAR ARCHIVO FINAL ===
with open("datos.json", "w", encoding="utf-8") as f:
    json.dump(estructura, f, ensure_ascii=False, indent=4)

print("\n✅ Archivo 'tareas_con_subtareas.json' generado correctamente.")
