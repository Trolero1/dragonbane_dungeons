# screen_editor.py - Editor visual de dungeons
#
# CORRECCIONES respecto a la versión anterior:
#  1. Eliminado el "Nivel Z" duplicado en el bucle de dibujado.
#  2. _ask_room_editor ahora llama a TextInput.update(dt) para que el cursor parpadee.
#  3. _ask_room_elements guarda copia de seguridad de los elementos antes de borrarlos
#     y los restaura si la selección queda incompleta (cancelación parcial).
#  4. _ask_new_salida: la dirección "especial" ya no usa DIR_DELTA (que daba (0,0,0)
#     y causaba que el destino fuera la propia room). En su lugar se muestra un
#     diálogo de selección de room destino entre todas las rooms del dungeon excepto
#     la propia. Los estados hacia/desde se preguntan igual que en otras direcciones.
#     La salida inversa desde la room destino se añade también como "especial".

import pygame
import copy
from constants import *
from ui_utils import (get_font, draw_text, Button, ScrollList,
                      QuestionWizard, ConfirmDialog, MessageDialog, TextInput)
from models import Dungeon, Room, Item, Monstruo, PNJ, Mecanismo, Salida, EfectoMecanismo
import persistence


def _map_to_screen(rx, ry, map_rect, offset_x, offset_y):
    """Convierte coordenadas lógicas a píxeles en pantalla."""
    cx = map_rect.x + map_rect.width // 2 + (rx + offset_x) * CELL_PX
    cy = map_rect.y + map_rect.height // 2 - (ry + offset_y) * CELL_PX
    return cx, cy


# ============================================================================
# FUNCIONES PARA CREAR ELEMENTOS
# ============================================================================

def _crear_item(screen, dungeon):
    """Crea un nuevo item."""
    questions = [
        {"key": "nombre", "prompt": "Nombre del item:", "type": "text"},
        {"key": "descripcion", "prompt": "Descripción:",
            "type": "text", "max_len": 200}
    ]

    text_zone = pygame.Rect(50, screen.get_height() - 200,
                            screen.get_width() - 100, 180)
    wiz = QuestionWizard(screen, text_zone, questions)
    clock = pygame.time.Clock()

    while not wiz.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            wiz.handle_event(event)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz.answers:
        return None

    item = Item()
    item.numero = dungeon.next_item_num()
    item.nombre = wiz.answers["nombre"]
    item.descripcion = wiz.answers["descripcion"]
    return item


def _crear_monstruo(screen, dungeon):
    """Crea un nuevo monstruo."""
    questions = [
        {"key": "nombre", "prompt": "Nombre del monstruo:", "type": "text"},
        {"key": "descripcion", "prompt": "Descripción:",
            "type": "text", "max_len": 200}
    ]

    text_zone = pygame.Rect(50, screen.get_height() - 200,
                            screen.get_width() - 100, 180)
    wiz = QuestionWizard(screen, text_zone, questions)
    clock = pygame.time.Clock()

    while not wiz.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            wiz.handle_event(event)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz.answers:
        return None

    monstruo = Monstruo()
    monstruo.numero = dungeon.next_monstruo_num()
    monstruo.nombre = wiz.answers["nombre"]
    monstruo.descripcion = wiz.answers["descripcion"]
    return monstruo


def _crear_pnj(screen, dungeon):
    """Crea un nuevo PNJ."""
    questions = [
        {"key": "nombre", "prompt": "Nombre del PNJ:", "type": "text"},
        {"key": "descripcion", "prompt": "Descripción:",
            "type": "text", "max_len": 200},
        {"key": "actitud", "prompt": "Actitud (hostil/neutral/aliado):",
         "type": "choice", "choices": ["hostil", "neutral", "aliado"], "default": "neutral"}
    ]

    text_zone = pygame.Rect(50, screen.get_height() - 200,
                            screen.get_width() - 100, 180)
    wiz = QuestionWizard(screen, text_zone, questions)
    clock = pygame.time.Clock()

    while not wiz.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            wiz.handle_event(event)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz.answers:
        return None

    pnj = PNJ()
    pnj.numero = dungeon.next_pnj_num()
    pnj.nombre = wiz.answers["nombre"]
    pnj.descripcion = wiz.answers["descripcion"]
    pnj.actitud = wiz.answers["actitud"]
    return pnj


def _crear_mecanismo(screen, dungeon, room_salidas):
    """Crea un nuevo mecanismo."""
    direcciones = [s.direccion for s in room_salidas] if room_salidas else []
    dir_str = ", ".join(
        direcciones) if direcciones else "ninguna (crea salidas primero)"

    questions = [
        {"key": "nombre", "prompt": "Nombre del mecanismo:", "type": "text"},
        {"key": "descripcion", "prompt": "Descripción:",
            "type": "text", "max_len": 200},
        {"key": "estado_inicial", "prompt": "Estado inicial (on/off):",
         "type": "choice", "choices": ["on", "off"], "default": "off"},
        {"key": "efecto_on", "prompt": "Efecto cuando está ON:",
         "type": "choice", "choices": MECH_EFFECTS, "default": "ninguno"},
        {"key": "efecto_off", "prompt": "Efecto cuando está OFF:",
         "type": "choice", "choices": MECH_EFFECTS, "default": "ninguno"},
    ]

    if direcciones:
        questions.append({
            "key": "direccion_on",
            "prompt": f"Dirección para efecto ON ({dir_str}):",
            "type": "choice", "choices": direcciones,
            "default": direcciones[0]
        })
        questions.append({
            "key": "direccion_off",
            "prompt": f"Dirección para efecto OFF ({dir_str}):",
            "type": "choice", "choices": direcciones,
            "default": direcciones[0]
        })

    text_zone = pygame.Rect(50, screen.get_height() - 200,
                            screen.get_width() - 100, 180)
    wiz = QuestionWizard(screen, text_zone, questions)
    clock = pygame.time.Clock()

    while not wiz.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            wiz.handle_event(event)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz.answers:
        return None

    mecanismo = Mecanismo()
    mecanismo.numero = dungeon.next_mecanismo_num()
    mecanismo.nombre = wiz.answers["nombre"]
    mecanismo.descripcion = wiz.answers["descripcion"]
    mecanismo.estado = wiz.answers["estado_inicial"]

    if wiz.answers.get("efecto_on") in ("abrir_salida", "cerrar_salida") and direcciones:
        mecanismo.efecto_on = EfectoMecanismo(
            tipo=wiz.answers["efecto_on"],
            direccion=wiz.answers.get("direccion_on", direcciones[0])
        )
    else:
        mecanismo.efecto_on = EfectoMecanismo(
            tipo=wiz.answers.get("efecto_on", "ninguno"))

    if wiz.answers.get("efecto_off") in ("abrir_salida", "cerrar_salida") and direcciones:
        mecanismo.efecto_off = EfectoMecanismo(
            tipo=wiz.answers["efecto_off"],
            direccion=wiz.answers.get("direccion_off", direcciones[0])
        )
    else:
        mecanismo.efecto_off = EfectoMecanismo(
            tipo=wiz.answers.get("efecto_off", "ninguno"))

    return mecanismo


def _pick_or_create_element(screen, dungeon, elementos_existentes, tipo, room_salidas=None):
    """Muestra lista de elementos existentes + opción 'Crear nuevo'."""
    W, H = screen.get_width(), screen.get_height()
    rect = pygame.Rect(W // 2 - 350, H // 2 - 200, 700, 400)

    labels = []
    for elem in elementos_existentes:
        if tipo == "item":
            labels.append(f"📦 #{elem.numero} {elem.nombre}")
        elif tipo == "monstruo":
            labels.append(f"👹 #{elem.numero} {elem.nombre}")
        elif tipo == "pnj":
            icono = "😊" if elem.actitud == "aliado" else (
                "😐" if elem.actitud == "neutral" else "👿")
            labels.append(
                f"{icono} #{elem.numero} {elem.nombre} ({elem.actitud})")
        elif tipo == "mecanismo":
            icono = "🔘" if elem.estado == "on" else "⭘"
            labels.append(f"{icono} #{elem.numero} {elem.nombre}")

    labels.append(f"✨ → CREAR NUEVO {tipo.upper()}")

    sl = ScrollList(rect, labels, font_size=14,
                    title=f"SELECCIONA {tipo.upper()}")
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

            idx = sl.handle_event(event)
            if idx is not None:
                if idx < len(elementos_existentes):
                    return copy.deepcopy(elementos_existentes[idx])
                else:
                    if tipo == "item":
                        nuevo = _crear_item(screen, dungeon)
                    elif tipo == "monstruo":
                        nuevo = _crear_monstruo(screen, dungeon)
                    elif tipo == "pnj":
                        nuevo = _crear_pnj(screen, dungeon)
                    elif tipo == "mecanismo":
                        nuevo = _crear_mecanismo(screen, dungeon, room_salidas)
                    else:
                        return None

                    if nuevo:
                        if tipo == "item":
                            dungeon.items_globales.append(nuevo)
                        elif tipo == "monstruo":
                            dungeon.monstruos_globales.append(nuevo)
                        elif tipo == "pnj":
                            dungeon.pnjs_globales.append(nuevo)
                        elif tipo == "mecanismo":
                            dungeon.mecanismos_globales.append(nuevo)
                        return copy.deepcopy(nuevo)
                    return None

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)
        sl.draw(screen)
        hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
        screen.blit(hint, (rect.x + 10, rect.bottom - 18))
        pygame.display.flip()
        clock.tick(30)


# ============================================================================
# FUNCIONES PARA EDITAR HABITACIONES
# ============================================================================

def _wrap_text_to_lines(text, font, max_width):
    """Parte 'text' en líneas que caben en max_width píxeles.
    Respeta también los saltos de línea explícitos (\\n) del texto.
    Devuelve lista de strings.
    """
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_multiline_input(surf, rect, text, font_size, active, cursor_visible, border_color):
    """Dibuja un campo de texto multilínea dentro de 'rect' con clipping estricto.
    Muestra solo las líneas que caben verticalmente; si hay más, hace scroll
    automático para que siempre sea visible la última línea (donde está el cursor).
    Devuelve el número de líneas totales (útil para calcular scroll si se necesita).
    """
    font = get_font(font_size)
    line_h = font_size + 4
    pad = 6

    # Fondo y borde
    pygame.draw.rect(surf, DARK_GRAY, rect, border_radius=4)
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=4)

    inner_w = rect.width - pad * 2
    inner_h = rect.height - pad * 2
    max_visible = max(1, inner_h // line_h)

    # Texto con cursor al final de la última línea
    display = text + ("_" if active and cursor_visible else "")
    lines = _wrap_text_to_lines(display, font, inner_w)

    # Scroll: mostrar siempre las últimas max_visible líneas
    start = max(0, len(lines) - max_visible)
    visible_lines = lines[start:]

    # Clip para que ningún glifo salga del rect
    old_clip = surf.get_clip()
    surf.set_clip(rect.inflate(-2, -2))

    for i, line in enumerate(visible_lines):
        s = font.render(line, True, WHITE)
        surf.blit(s, (rect.x + pad, rect.y + pad + i * line_h))

    surf.set_clip(old_clip)
    return len(lines)


def _ask_room_editor(screen, room):
    """Diálogo para editar nombre y descripción de una habitación.
    CORREGIDO:
    - Se llama a update(dt) en cada input para que el cursor parpadee.
    - La descripción usa un campo multilínea con clipping: el texto nunca
      sale del cuadro y hace scroll automático hacia la última línea.
    - El diálogo es más alto para que el campo de descripción tenga espacio.
    """
    W, H = screen.get_width(), screen.get_height()
    # Diálogo más alto para acomodar el campo de descripción multilínea
    rect = pygame.Rect(W // 2 - 400, H // 2 - 200, 800, 400)

    # Campo de nombre (una línea, usa TextInput normal)
    name_input = TextInput((rect.x + 10, rect.y + 50, rect.width - 20, 35),
                           prompt="", font_size=18, max_len=50)
    name_input.text = room.nombre
    name_input.active = True

    # Campo de descripción multilínea (gestionado manualmente)
    desc_rect = pygame.Rect(rect.x + 10, rect.y + 130, rect.width - 20, 180)
    desc_text = room.descripcion
    desc_active = False
    desc_max_len = 500

    # Estado del cursor para la descripción
    cursor_timer = 0
    cursor_visible = True

    done = False
    clock = pygame.time.Clock()

    while not done:
        dt = clock.tick(30)
        cursor_timer += dt
        if cursor_timer > 500:
            cursor_visible = not cursor_visible
            cursor_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_RETURN:
                    if desc_active:
                        # En el campo multilínea ENTER añade salto de línea
                        if len(desc_text) < desc_max_len:
                            desc_text += "\n"
                    else:
                        # En el campo nombre ENTER confirma el diálogo
                        done = True
                if event.key == pygame.K_TAB:
                    name_input.active = not name_input.active
                    desc_active = not desc_active
                if desc_active:
                    if event.key == pygame.K_BACKSPACE:
                        desc_text = desc_text[:-1]
                    elif event.key not in (pygame.K_RETURN, pygame.K_TAB,
                                           pygame.K_ESCAPE):
                        if len(desc_text) < desc_max_len and event.unicode.isprintable():
                            desc_text += event.unicode

            # Clic activa el campo correspondiente
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if desc_rect.collidepoint(event.pos):
                    desc_active = True
                    name_input.active = False
                elif name_input.rect.collidepoint(event.pos):
                    name_input.active = True
                    desc_active = False

            name_input.handle_event(event)

        name_input.update(dt)

        # ── Dibujado ──────────────────────────────────────────────────────────
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(screen, GOLD, rect, 2, border_radius=8)

        draw_text(screen, f"EDITAR HABITACIÓN #{room.numero}",
                  rect.x + 10, rect.y + 10, 18, GOLD, bold=True)

        draw_text(screen, "Nombre:", rect.x + 10, rect.y + 35, 14, WHITE)
        name_input.draw(screen)

        chars_left = desc_max_len - len(desc_text)
        desc_label = f"Descripción  ({chars_left} caracteres restantes):"
        draw_text(screen, desc_label, rect.x + 10, rect.y + 112, 13, WHITE)

        border_col = YELLOW if desc_active else MID_GRAY
        _draw_multiline_input(screen, desc_rect, desc_text,
                              font_size=15, active=desc_active,
                              cursor_visible=cursor_visible,
                              border_color=border_col)

        hint = ("TAB: cambiar campo | ENTER en nombre: guardar | "
                "ENTER en descripción: nueva línea | ESC: cancelar")
        draw_text(screen, hint, rect.x + 10, rect.y + 368, 11, MID_GRAY)

        pygame.display.flip()

    room.nombre = name_input.text.strip() or f"Habitación {room.numero}"
    room.descripcion = desc_text.strip()
    return True


def _pick_room_destino_especial(screen, dungeon, room_origen):
    """Muestra lista de todas las rooms del dungeon (excepto la de origen)
    para que el usuario elija el destino de una salida especial.
    Devuelve la Room seleccionada o None si se cancela.
    """
    otras_rooms = [r for r in dungeon.rooms if r.id != room_origen.id]

    if not otras_rooms:
        MessageDialog(screen,
                      "No hay otras habitaciones en el dungeon.\n"
                      "Crea al menos una habitación más antes de añadir "
                      "una salida especial.").run()
        return None

    W, H = screen.get_width(), screen.get_height()
    rect = pygame.Rect(W // 2 - 350, H // 2 - 220, 700, 440)

    labels = [
        f"#{r.numero}  {r.nombre}  ({r.x}, {r.y}, {r.z})"
        for r in otras_rooms
    ]

    sl = ScrollList(rect, labels, font_size=14,
                    title="ELIGE HABITACIÓN DESTINO (salida especial)")
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

            idx = sl.handle_event(event)
            if idx is not None:
                return otras_rooms[idx]

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)
        sl.draw(screen)
        hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
        screen.blit(hint, (rect.x + 10, rect.bottom - 18))
        pygame.display.flip()
        clock.tick(30)


def _ask_new_salida(screen, room, dungeon):
    """Wizard para añadir una nueva salida.

    Paso 1 — lista con ScrollList (ESC o "↩ VOLVER" cancelan sin tocar nada).
    Paso 2 — si es 'especial', selección de room destino.
    Paso 3 — estados hacia/desde con QuestionWizard (ESC cancela limpiamente).
    """
    disponibles = [d for d in DIRECTIONS if room.salida_en(d) is None]

    if not disponibles:
        MessageDialog(screen,
                      "Esta habitación ya tiene todas las salidas posibles (7).").run()
        return None

    # ── Paso 1: elegir dirección con ScrollList ───────────────────────────────
    W, H = screen.get_width(), screen.get_height()
    list_rect = pygame.Rect(W // 2 - 280, H // 2 - 220, 560, 440)

    VOLVER = "↩  VOLVER"
    iconos = {
        "norte": "⬆", "sur": "⬇", "este": "➡", "oeste": "⬅",
        "arriba": "🔼", "abajo": "🔽", "especial": "✨",
    }
    labels_dir = [f"{iconos.get(d, '')}  {d.upper()}" for d in disponibles]
    labels_dir.append(VOLVER)

    sl_dir = ScrollList(list_rect, labels_dir, font_size=15,
                        title="AÑADIR SALIDA — elige dirección")
    clock = pygame.time.Clock()
    direccion = None

    while direccion is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

            idx = sl_dir.handle_event(event)
            if idx is not None:
                if idx >= len(disponibles):   # pulsó VOLVER
                    return None
                direccion = disponibles[idx]

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, DARK_GRAY, list_rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, list_rect, 2, border_radius=6)
        sl_dir.draw(screen)
        hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
        screen.blit(hint, (list_rect.x + 10, list_rect.bottom - 18))
        pygame.display.flip()
        clock.tick(30)

    # ── Paso 2: elegir room destino (solo para "especial") ────────────────────
    room_nueva = None  # rastrea si creamos una room nueva para poder deshacer

    if direccion == "especial":
        dest_room = _pick_room_destino_especial(screen, dungeon, room)
        if dest_room is None:
            return None
    else:
        dx, dy, dz = DIR_DELTA.get(direccion, (0, 0, 0))
        dest_room = dungeon.room_en(room.x + dx, room.y + dy, room.z + dz)

        if dest_room is None:
            dest_room = Room()
            dest_room.numero = dungeon.next_room_num()
            dest_room.x = room.x + dx
            dest_room.y = room.y + dy
            dest_room.z = room.z + dz
            dest_room.nombre = f"Habitación {dest_room.numero}"
            dungeon.rooms.append(dest_room)
            room_nueva = dest_room  # recordar para deshacer si se cancela
            MessageDialog(screen,
                          f"Se ha creado una nueva habitación en {direccion}.").run()

    def _cancelar_paso3():
        """Deshace la room recién creada si el usuario cancela en el paso 3."""
        if room_nueva and room_nueva in dungeon.rooms:
            dungeon.rooms.remove(room_nueva)
            dungeon._next_room -= 1
        return None

    # ── Paso 3: preguntar estados hacia/desde ─────────────────────────────────
    text_zone = pygame.Rect(50, screen.get_height() - 200,
                            screen.get_width() - 100, 180)

    questions_estado = [
        {"key": "estado_hacia",
         "prompt": f"Estado hacia '{dest_room.nombre}' (puede pasar el grupo):",
         "type": "choice", "choices": ["abierta", "cerrada"], "default": "abierta"},
        {"key": "estado_desde",
         "prompt": f"Estado desde '{dest_room.nombre}' (pueden volver):",
         "type": "choice", "choices": ["abierta", "cerrada"], "default": "abierta"},
    ]

    wiz_estado = QuestionWizard(screen, text_zone, questions_estado)

    while not wiz_estado.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return _cancelar_paso3()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return _cancelar_paso3()
            wiz_estado.handle_event(event)

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz_estado.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz_estado.answers:
        return _cancelar_paso3()

    estado_hacia = wiz_estado.answers.get("estado_hacia", "abierta")
    estado_desde = wiz_estado.answers.get("estado_desde", "abierta")

    # ── Crear salida en la room origen ────────────────────────────────────────
    salida = Salida(
        direccion=direccion,
        room_destino_id=dest_room.id,
        estado_hacia_destino=estado_hacia,
        estado_hacia_origen=estado_desde,
    )
    room.salidas.append(salida)

    # ── Crear salida inversa en la room destino ───────────────────────────────
    # Para direcciones normales usamos la opuesta; para "especial" → "especial"
    dir_inversa = OPPOSITE[direccion]  # "especial" → "especial"

    # Solo añadir la inversa si la room destino no tiene ya una salida en esa dirección
    if dest_room.salida_en(dir_inversa) is None:
        salida_inv = Salida(
            direccion=dir_inversa,
            room_destino_id=room.id,
            estado_hacia_destino=estado_desde,
            estado_hacia_origen=estado_hacia,
        )
        dest_room.salidas.append(salida_inv)

    return salida


def _gestionar_salidas(screen, room, dungeon):
    """Pantalla de gestión de salidas de una habitación.

    Muestra un ScrollList con las salidas existentes más AÑADIR y VOLVER.
    Al elegir una salida existente aparece un submenú para:
      - Cambiar estado hacia el destino (abierta/cerrada).
      - Cambiar estado desde el destino (abierta/cerrada).
      - Eliminar la salida (y su inversa si existe).
    Al elegir AÑADIR se llama al wizard _ask_new_salida.
    ESC o VOLVER regresan al editor principal.
    """
    clock = pygame.time.Clock()
    W, H = screen.get_width(), screen.get_height()
    list_rect = pygame.Rect(W // 2 - 340, H // 2 - 260, 680, 500)

    ANADIR = "➕  AÑADIR NUEVA SALIDA"
    VOLVER = "↩  VOLVER"

    def build_labels():
        items = []
        for s in room.salidas:
            dest = dungeon.room_por_id(s.room_destino_id)
            dest_nom = (dest.nombre if dest else "???")[:22]
            hacia = "✅" if s.estado_hacia_destino == "abierta" else "🔒"
            desde = "✅" if s.estado_hacia_origen == "abierta" else "🔒"
            items.append(
                f"[{s.direccion.upper():8s}]  {dest_nom:<22}  →{hacia}  ←{desde}"
            )
        items.append(ANADIR)
        items.append(VOLVER)
        return items

    def submenú(salida):
        """Submenú de acciones sobre una salida concreta. Devuelve True si hubo cambio."""
        dest = dungeon.room_por_id(salida.room_destino_id)
        dest_nom = dest.nombre if dest else "???"
        sub_rect = pygame.Rect(W // 2 - 320, H // 2 - 150, 640, 310)

        def opciones():
            hacia_txt = salida.estado_hacia_destino
            desde_txt = salida.estado_hacia_origen
            return [
                f"Cambiar HACIA '{dest_nom[:24]}'   (ahora: {hacia_txt})",
                f"Cambiar DESDE '{dest_nom[:24]}'   (ahora: {desde_txt})",
                f"🗑  Eliminar esta salida  [{salida.direccion}]",
                "↩  Volver",
            ]

        while True:
            sl = ScrollList(sub_rect, opciones(), font_size=14,
                            title=f"SALIDA {salida.direccion.upper()} → {dest_nom}")
            idx_sub = None
            while idx_sub is None:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        return False
                    i = sl.handle_event(event)
                    if i is not None:
                        idx_sub = i

                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 210))
                screen.blit(overlay, (0, 0))
                pygame.draw.rect(screen, DARK_GRAY, sub_rect, border_radius=6)
                pygame.draw.rect(screen, GOLD, sub_rect, 2, border_radius=6)
                sl.draw(screen)
                hint = get_font(12).render("ESC para volver", True, MID_GRAY)
                screen.blit(hint, (sub_rect.x + 10, sub_rect.bottom - 18))
                pygame.display.flip()
                clock.tick(30)

            if idx_sub == 0:   # toggle hacia
                nuevo = "cerrada" if salida.estado_hacia_destino == "abierta" else "abierta"
                salida.estado_hacia_destino = nuevo
                if dest:
                    inv = dest.salida_en(OPPOSITE.get(salida.direccion, ""))
                    if inv and inv.room_destino_id == room.id:
                        inv.estado_hacia_origen = nuevo
                # continuar bucle para mostrar valor actualizado

            elif idx_sub == 1:  # toggle desde
                nuevo = "cerrada" if salida.estado_hacia_origen == "abierta" else "abierta"
                salida.estado_hacia_origen = nuevo
                if dest:
                    inv = dest.salida_en(OPPOSITE.get(salida.direccion, ""))
                    if inv and inv.room_destino_id == room.id:
                        inv.estado_hacia_destino = nuevo

            elif idx_sub == 2:  # eliminar
                if ConfirmDialog(
                        screen,
                        f"¿Eliminar la salida [{salida.direccion}] "
                        f"hacia \'{dest_nom}\'?\n"
                        "También se eliminará la salida inversa si existe.").run():
                    if dest:
                        dir_inv = OPPOSITE.get(salida.direccion, "")
                        inv = dest.salida_en(dir_inv)
                        if inv and inv.room_destino_id == room.id:
                            dest.salidas.remove(inv)
                    room.salidas.remove(salida)
                    return True   # salida eliminada, volver a lista principal
                # si cancela confirmación, volvemos al submenú

            elif idx_sub == 3:  # volver
                return False

    # ── Bucle principal ───────────────────────────────────────────────────────
    while True:
        labels = build_labels()
        sl_main = ScrollList(list_rect, labels, font_size=14,
                             title=f"SALIDAS — {room.nombre}  ({len(room.salidas)}/7)")
        selected = None
        while selected is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                i = sl_main.handle_event(event)
                if i is not None:
                    selected = i

            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            pygame.draw.rect(screen, DARK_GRAY, list_rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, list_rect, 2, border_radius=6)
            sl_main.draw(screen)
            hint = get_font(12).render(
                "ESC para volver al editor", True, MID_GRAY)
            screen.blit(hint, (list_rect.x + 10, list_rect.bottom - 18))
            pygame.display.flip()
            clock.tick(30)

        n_sal = len(room.salidas)

        if selected > n_sal:          # VOLVER
            return
        elif selected == n_sal:       # AÑADIR NUEVA SALIDA
            _ask_new_salida(screen, room, dungeon)
        else:
            # Salida existente: submenú
            submenú(room.salidas[selected])
        # vuelve al bucle para refrescar la lista


def _ask_room_elements(screen, room, dungeon):
    """Wizard para configurar items, monstruos, PNJs y mecanismos.

    CORREGIDO: se hace una copia de seguridad de los elementos existentes
    antes de limpiar las listas. Si la selección queda incompleta (el usuario
    cancela a mitad), se restauran los elementos originales en lugar de dejar
    la room vacía.
    """
    W, H = screen.get_width(), screen.get_height()

    questions = [
        {"key": "n_items",
         "prompt": "Número de items (0-3):", "type": "int",
         "min": 0, "max": 3, "default": 0},
        {"key": "n_monstruos",
         "prompt": "Número de monstruos (0-3):", "type": "int",
         "min": 0, "max": 3, "default": 0},
        {"key": "n_pnjs",
         "prompt": "Número de PNJs (0-3):", "type": "int",
         "min": 0, "max": 3, "default": 0},
        {"key": "n_mecanismos",
         "prompt": "Número de mecanismos (0-3):", "type": "int",
         "min": 0, "max": 3, "default": 0},
    ]

    text_zone = pygame.Rect(50, H - 200, W - 100, 180)
    wiz = QuestionWizard(screen, text_zone, questions)
    clock = pygame.time.Clock()

    while not wiz.finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            wiz.handle_event(event)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        wiz.draw()
        pygame.display.flip()
        clock.tick(30)

    if not wiz.answers:
        return False

    # FIX: guardar copia antes de limpiar por si la selección se cancela a mitad
    backup_items = room.items[:]
    backup_monstruos = room.monstruos[:]
    backup_pnjs = room.pnjs[:]
    backup_mecanismos = room.mecanismos[:]

    room.items = []
    room.monstruos = []
    room.pnjs = []
    room.mecanismos = []

    cancelled = False

    for _ in range(wiz.answers.get("n_items", 0)):
        elemento = _pick_or_create_element(
            screen, dungeon, dungeon.items_globales, "item")
        if elemento is None:
            cancelled = True
            break
        room.items.append(elemento)

    if not cancelled:
        for _ in range(wiz.answers.get("n_monstruos", 0)):
            elemento = _pick_or_create_element(
                screen, dungeon, dungeon.monstruos_globales, "monstruo")
            if elemento is None:
                cancelled = True
                break
            room.monstruos.append(elemento)

    if not cancelled:
        for _ in range(wiz.answers.get("n_pnjs", 0)):
            elemento = _pick_or_create_element(
                screen, dungeon, dungeon.pnjs_globales, "pnj")
            if elemento is None:
                cancelled = True
                break
            room.pnjs.append(elemento)

    if not cancelled:
        for _ in range(wiz.answers.get("n_mecanismos", 0)):
            elemento = _pick_or_create_element(
                screen, dungeon, dungeon.mecanismos_globales, "mecanismo",
                room.salidas)
            if elemento is None:
                cancelled = True
                break
            room.mecanismos.append(elemento)

    if cancelled:
        # Restaurar estado previo
        room.items = backup_items
        room.monstruos = backup_monstruos
        room.pnjs = backup_pnjs
        room.mecanismos = backup_mecanismos
        return False

    return True


# ============================================================================
# FUNCIÓN PRINCIPAL DEL EDITOR
# ============================================================================

def run_editor(screen, dungeon: Dungeon):
    """Editor visual de dungeons."""
    clock = pygame.time.Clock()
    W, H = screen.get_size()

    top_h = H * 2 // 3
    bot_h = H - top_h
    map_w = W * 2 // 3
    elem_w = W - map_w

    map_rect = pygame.Rect(0, 0, map_w, top_h)
    elements_rect = pygame.Rect(map_w, 0, elem_w, top_h)
    text_zone = pygame.Rect(0, top_h, W, bot_h)

    z_level = 0
    offset_x = offset_y = 0
    selected_room_id = None

    if not dungeon.rooms:
        r0 = Room()
        r0.numero = dungeon.next_room_num()
        r0.x = r0.y = r0.z = 0
        r0.nombre = "Habitación Inicial"
        dungeon.rooms.append(r0)
        selected_room_id = r0.id

    btn_z_up = Button(
        (map_rect.right - 80, map_rect.bottom - 45, 35, 30), "▲", font_size=12)
    btn_z_down = Button(
        (map_rect.right - 40, map_rect.bottom - 45, 35, 30), "▼", font_size=12)
    btn_z_reset = Button(
        (map_rect.right - 120, map_rect.bottom - 45, 35, 30), "0", font_size=12)

    btn_edit_room = Button(
        (elements_rect.x + 10, elements_rect.y + 60, elem_w - 20, 35),
        "✏ Editar Habitación", font_size=12)
    btn_edit_exits = Button(
        (elements_rect.x + 10, elements_rect.y + 100, elem_w - 20, 35),
        "🚪 Editar Salidas", font_size=12)
    btn_delete_room = Button(
        (elements_rect.x + 10, elements_rect.y + 140, elem_w - 20, 35),
        "🗑 Eliminar Habitación", font_size=12, color=C_ERROR)
    btn_elements = Button(
        (elements_rect.x + 10, elements_rect.y + 180, elem_w - 20, 35),
        "⚙ Configurar Elementos", font_size=12)

    help_lines = [
        "EDITOR DE DUNGEON",
        "Click izquierdo: seleccionar habitación",
        "Click derecho: centrar mapa en habitación seleccionada",
        "Rueda ratón: desplazar mapa | Botón central: arrastrar | ESC: guardar y salir",
    ]

    running = True
    drag_start = None
    dragging = False
    drag_offset = (0, 0)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.MOUSEWHEEL:
                if map_rect.collidepoint(pygame.mouse.get_pos()):
                    offset_y += event.y
                    offset_x += event.x

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                dragging = True
                drag_start = pygame.mouse.get_pos()
                drag_offset = (offset_x, offset_y)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                dragging = False

            if event.type == pygame.MOUSEMOTION and dragging:
                mx, my = pygame.mouse.get_pos()
                dx = (mx - drag_start[0]) // CELL_PX
                dy = (my - drag_start[1]) // CELL_PX
                offset_x = drag_offset[0] + dx
                offset_y = drag_offset[1] - dy

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Controles Z (tienen prioridad sobre el mapa)
                if btn_z_up.rect.collidepoint(mx, my):
                    z_level += 1
                    selected_room_id = None
                elif btn_z_down.rect.collidepoint(mx, my):
                    z_level -= 1
                    selected_room_id = None
                elif btn_z_reset.rect.collidepoint(mx, my):
                    z_level = 0
                    selected_room_id = None
                elif map_rect.collidepoint(mx, my):
                    clicked_room = None
                    for room in dungeon.rooms:
                        if room.z != z_level:
                            continue
                        cx, cy = _map_to_screen(
                            room.x, room.y, map_rect, offset_x, offset_y)
                        rr = pygame.Rect(
                            cx - ROOM_SIZE // 2, cy - ROOM_SIZE // 2,
                            ROOM_SIZE, ROOM_SIZE)
                        if rr.collidepoint(mx, my):
                            clicked_room = room
                            break
                    selected_room_id = clicked_room.id if clicked_room else None

                elif elements_rect.collidepoint(mx, my):
                    if btn_edit_room.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                _ask_room_editor(screen, room)
                    elif btn_edit_exits.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                _gestionar_salidas(screen, room, dungeon)
                    elif btn_delete_room.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                if len(dungeon.rooms) <= 1:
                                    MessageDialog(
                                        screen,
                                        "No se puede eliminar la última habitación."
                                    ).run()
                                elif ConfirmDialog(
                                        screen,
                                        f"¿Eliminar habitación '{room.nombre}'?").run():
                                    for r in dungeon.rooms:
                                        for s in r.salidas[:]:
                                            if s.room_destino_id == room.id:
                                                r.salidas.remove(s)
                                    dungeon.rooms.remove(room)
                                    selected_room_id = None
                    elif btn_elements.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                _ask_room_elements(screen, room, dungeon)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if selected_room_id:
                    room = dungeon.room_por_id(selected_room_id)
                    if room:
                        offset_x = -room.x
                        offset_y = room.y

        # ── Dibujado ──────────────────────────────────────────────────────────
        screen.fill(BLACK)

        # Mapa
        pygame.draw.rect(screen, BG_MAP, map_rect)
        pygame.draw.rect(screen, MID_GRAY, map_rect, 1)

        rooms_z = [r for r in dungeon.rooms if r.z == z_level]

        # Líneas de conexión entre rooms del mismo nivel Z
        for room in rooms_z:
            cx, cy = _map_to_screen(
                room.x, room.y, map_rect, offset_x, offset_y)
            for salida in room.salidas:
                if salida.direccion in ("arriba", "abajo", "especial"):
                    continue
                dest = dungeon.room_por_id(salida.room_destino_id)
                if dest and dest.z == z_level:
                    dx2, dy2 = _map_to_screen(
                        dest.x, dest.y, map_rect, offset_x, offset_y)
                    color = GREEN if salida.estado_hacia_destino == "abierta" else RED
                    pygame.draw.line(screen, color, (cx, cy), (dx2, dy2), 2)

        # Rectángulos de rooms
        for room in rooms_z:
            cx, cy = _map_to_screen(
                room.x, room.y, map_rect, offset_x, offset_y)
            rr = pygame.Rect(cx - ROOM_SIZE // 2, cy - ROOM_SIZE // 2,
                             ROOM_SIZE, ROOM_SIZE)

            if not map_rect.colliderect(rr.inflate(20, 20)):
                continue

            fill = (80, 80, 100) if room.id == selected_room_id else ROOM_FILL
            pygame.draw.rect(screen, fill, rr)
            pygame.draw.rect(screen, ROOM_BORDER, rr, 2)

            # Indicador de salidas especiales / arriba-abajo
            tiene_especial = any(
                s.direccion == "especial" for s in room.salidas)
            tiene_vertical = any(s.direccion in ("arriba", "abajo")
                                 for s in room.salidas)
            if tiene_especial:
                pygame.draw.circle(screen, ORANGE, (rr.right - 5, rr.y + 5), 4)
            if tiene_vertical:
                pygame.draw.circle(screen, BLUE, (rr.right - 5, rr.y + 14), 4)

            font = get_font(10)
            ns = font.render(str(room.numero), True, YELLOW)
            screen.blit(ns, (rr.x + 2, rr.y + 2))
            name_s = font.render(room.nombre[:10], True, LIGHT_GRAY)
            screen.blit(name_s, (rr.x + 2, rr.y + 14))

        # Controles Z
        btn_z_up.draw(screen)
        btn_z_down.draw(screen)
        btn_z_reset.draw(screen)

        # FIX: nivel Z mostrado una sola vez (eliminado el duplicado)
        z_text = get_font(12).render(f"Nivel Z: {z_level}", True, GOLD)
        screen.blit(z_text, (map_rect.right - 85, map_rect.bottom - 25))

        # Panel de elementos
        pygame.draw.rect(screen, BG_PANEL, elements_rect)
        pygame.draw.rect(screen, MID_GRAY, elements_rect, 1)
        draw_text(screen, "EDITOR", elements_rect.x + 10,
                  elements_rect.y + 8, 14, GOLD, bold=True)

        if selected_room_id:
            room = dungeon.room_por_id(selected_room_id)
            if room:
                y = elements_rect.y + 32
                draw_text(screen, f"Habitación #{room.numero}",
                          elements_rect.x + 8, y, 13, YELLOW, bold=True)
                y += 18
                draw_text(screen, f"Nombre: {room.nombre}",
                          elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen, f"Coord: ({room.x}, {room.y}, {room.z})",
                          elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen, f"Salidas: {len(room.salidas)}/7",
                          elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen,
                          f"Items: {len(room.items)} | Monstruos: {len(room.monstruos)}",
                          elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen,
                          f"PNJs: {len(room.pnjs)} | Mecanismos: {len(room.mecanismos)}",
                          elements_rect.x + 8, y, 11, WHITE)

                btn_edit_room.rect.y = elements_rect.y + 140
                btn_edit_exits.rect.y = elements_rect.y + 180
                btn_delete_room.rect.y = elements_rect.y + 220
                btn_elements.rect.y = elements_rect.y + 260

                btn_edit_room.draw(screen)
                btn_edit_exits.draw(screen)
                btn_delete_room.draw(screen)
                btn_elements.draw(screen)
        else:
            draw_text(screen, "Selecciona una habitación",
                      elements_rect.x + 8, elements_rect.y + 60, 12, MID_GRAY)

        # Leyenda de indicadores visuales
        ley_y = elements_rect.y + 310
        pygame.draw.circle(
            screen, ORANGE, (elements_rect.x + 14, ley_y + 4), 4)
        draw_text(screen, "salida especial",
                  elements_rect.x + 22, ley_y, 10, MID_GRAY)
        ley_y += 14
        pygame.draw.circle(screen, BLUE, (elements_rect.x + 14, ley_y + 4), 4)
        draw_text(screen, "arriba/abajo",
                  elements_rect.x + 22, ley_y, 10, MID_GRAY)

        # Zona de ayuda
        pygame.draw.rect(screen, BG_TEXT, text_zone)
        pygame.draw.rect(screen, MID_GRAY, text_zone, 1)
        for i, line in enumerate(help_lines):
            draw_text(screen, line, text_zone.x + 10,
                      text_zone.y + 8 + i * 18, 13, MID_GRAY)

        title_s = get_font(14, bold=True).render(
            f"EDITOR: {dungeon.nombre}", True, GOLD)
        screen.blit(title_s, (8, 4))

        pygame.display.flip()
        clock.tick(60)
    # <--- Nueva línea de seguridad introducida el 2-5-26
    dungeon.validar_y_reparar_ids()
    persistence.guardar_dungeon(dungeon)
    return dungeon
