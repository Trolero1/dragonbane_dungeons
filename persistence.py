# persistence.py - Guardado y carga de dungeons

import json
import os
from datetime import datetime
from models import Dungeon
from constants import DUNGEONS_DIR, DATA_DIR

# ══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE NÚMEROS DE DUNGEON
# ══════════════════════════════════════════════════════════════════════════════

META_FILE = os.path.join(
    DATA_DIR, "meta.json") if 'DATA_DIR' in dir() else None


def _cargar_meta():
    """Carga el archivo de metadatos con el próximo número de dungeon."""
    if not os.path.exists(META_FILE):
        return {"next_dungeon_num": 1}
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"next_dungeon_num": 1}


def _guardar_meta(meta):
    """Guarda el archivo de metadatos."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def obtener_siguiente_numero_dungeon():
    """Devuelve el siguiente número disponible para un nuevo dungeon."""
    meta = _cargar_meta()
    num = meta.get("next_dungeon_num", 1)
    # Avanzamos para la próxima vez
    meta["next_dungeon_num"] = num + 1
    _guardar_meta(meta)
    return num


def obtener_numero_dungeon_existente(dungeon_id):
    """Obtiene el número de un dungeon existente (de su archivo)."""
    path = os.path.join(DUNGEONS_DIR, f"{dungeon_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("numero", 0)
    except:
        return 0


def actualizar_numero_dungeon(dungeon_id, numero):
    """Actualiza el número de un dungeon en su archivo."""
    path = os.path.join(DUNGEONS_DIR, f"{dungeon_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        d["numero"] = numero
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except:
        pass


def guardar_dungeon(dungeon: Dungeon):
    """Guarda un dungeon en un archivo JSON."""
    if not dungeon.fecha_creacion:
        dungeon.fecha_creacion = datetime.now().strftime("%d/%m/%Y %H:%M")

    path = os.path.join(DUNGEONS_DIR, f"{dungeon.id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dungeon.to_dict(), f, ensure_ascii=False, indent=2)


def cargar_dungeon(dungeon_id: str) -> Dungeon:
    """Carga un dungeon desde su archivo JSON."""
    path = os.path.join(DUNGEONS_DIR, f"{dungeon_id}.json")

    with open(path, "r", encoding="utf-8") as f:
        return Dungeon.from_dict(json.load(f))


def listar_dungeons() -> list[dict]:
    """Devuelve lista de {id, nombre, fecha_creacion, num_rooms}."""
    result = []

    if not os.path.isdir(DUNGEONS_DIR):
        return result

    for fname in os.listdir(DUNGEONS_DIR):
        if fname.endswith(".json"):
            path = os.path.join(DUNGEONS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                result.append({
                    "id": d.get("id", fname.replace(".json", "")),
                    "numero": d.get("numero", 0),  # ← Añadir
                    "nombre": d.get("nombre", "?"),
                    "fecha_creacion": d.get("fecha_creacion", "?"),
                    "num_rooms": len(d.get("rooms", [])),
                })
            except Exception:
                pass

    result.sort(key=lambda x: x["numero"])
    return result


def eliminar_dungeon(dungeon_id: str):
    """Elimina el archivo JSON de un dungeon."""
    path = os.path.join(DUNGEONS_DIR, f"{dungeon_id}.json")
    if os.path.exists(path):
        os.remove(path)
