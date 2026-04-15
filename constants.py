# constants.py - Configuración global del Editor de Dungeons Dragonbane

import os


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — RUTAS DE CARPETAS
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DUNGEONS_DIR = os.path.join(DATA_DIR, "dungeons")

os.makedirs(DUNGEONS_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONFIGURACIÓN DE PANTALLA
# ══════════════════════════════════════════════════════════════════════════════

SCREEN_W = 1400
SCREEN_H = 900
FPS = 60
TITLE = "DRAGONBANE"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — COLORES
# ══════════════════════════════════════════════════════════════════════════════

# Colores base
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
DARK_GRAY = (40, 40, 40)
MID_GRAY = (100, 100, 100)
GREEN = (50, 200, 80)
RED = (200, 50, 50)
YELLOW = (220, 200, 50)
BLUE = (60, 120, 220)
ORANGE = (220, 130, 40)
LIGHT_GRAY = (200, 200, 200)
GOLD = (212, 175, 55)
DEEP_RED = (120, 20, 20)

# Colores Dragonbane
C_FONDO = (26, 16, 8)
C_PANEL = (42, 28, 14)
C_TITULO = (200, 146, 42)
C_SUBTITULO = (224, 192, 112)
C_TEXTO = (240, 230, 200)
C_TEXTO_DIM = (154, 128, 96)
C_BOTON = (90, 48, 16)
C_BOTON_HOV = (138, 80, 32)
C_BOTON_SEL = (200, 146, 42)
C_BOTON_TXT = (240, 230, 200)
C_BORDE = (106, 72, 32)
C_SEPARADOR = (74, 48, 16)
C_ENTRADA = (58, 37, 16)
C_ENTRADA_SEL = (90, 58, 16)
C_ERROR = (200, 80, 32)
C_VERDE = (80, 180, 80)

# Colores del editor de dungeons
ROOM_FILL = (60, 60, 60)
ROOM_BORDER = (200, 200, 200)
BG_MAP = (10, 10, 10)
BG_PANEL = (5, 5, 15)
BG_TEXT = (5, 5, 5)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — TAMAÑOS DEL MAPA
# ══════════════════════════════════════════════════════════════════════════════

ROOM_SIZE = 48
ROOM_GAP = 40
CELL_PX = ROOM_SIZE + ROOM_GAP


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — DIRECCIONES
# ══════════════════════════════════════════════════════════════════════════════

DIRECTIONS = ["norte", "sur", "este", "oeste", "arriba", "abajo", "especial"]

DIR_DELTA = {
    "norte": (0, 1, 0), "sur": (0, -1, 0), "este": (1, 0, 0), "oeste": (-1, 0, 0),
    "arriba": (0, 0, 1), "abajo": (0, 0, -1), "especial": (0, 0, 0),
}

OPPOSITE = {
    "norte": "sur", "sur": "norte", "este": "oeste", "oeste": "este",
    "arriba": "abajo", "abajo": "arriba", "especial": "especial",
}


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — ESTADOS POSIBLES
# ══════════════════════════════════════════════════════════════════════════════

ITEM_STATES = ["en_room", "en_inventario", "destruido"]
MECH_STATES = ["on", "off", "destruido"]
PNJ_ATTITUDES = ["hostil", "neutral", "aliado"]
EXIT_STATES = ["abierta", "cerrada"]


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — EFECTOS DE MECANISMOS
# ══════════════════════════════════════════════════════════════════════════════

MECH_EFFECTS = [
    "ninguno", "daño_personaje", "cura_personaje",
    "dar_monedas", "dar_item", "abrir_salida", "cerrar_salida"
]