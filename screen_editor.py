# screen_editor.py - Editor visual de dungeons

import pygame
import copy
from constants import *
from ui_utils import get_font, draw_text, Button, ScrollList, QuestionWizard, ConfirmDialog, MessageDialog, TextInput
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

    text_zone = pygame.Rect(50, screen.get_height() -
                            200, screen.get_width() - 100, 180)
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

    text_zone = pygame.Rect(50, screen.get_height() -
                            200, screen.get_width() - 100, 180)
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

    text_zone = pygame.Rect(50, screen.get_height() -
                            200, screen.get_width() - 100, 180)
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
        questions.append({"key": "direccion_on", "prompt": f"Dirección para efecto ON ({dir_str}):",
                         "type": "choice", "choices": direcciones, "default": direcciones[0] if direcciones else ""})
        questions.append({"key": "direccion_off", "prompt": f"Dirección para efecto OFF ({dir_str}):",
                         "type": "choice", "choices": direcciones, "default": direcciones[0] if direcciones else ""})

    text_zone = pygame.Rect(50, screen.get_height() -
                            200, screen.get_width() - 100, 180)
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

def _ask_room_editor(screen, room):
    """Diálogo para editar nombre y descripción de una habitación."""
    W, H = screen.get_width(), screen.get_height()
    rect = pygame.Rect(W // 2 - 400, H // 2 - 150, 800, 300)

    name_input = TextInput((rect.x + 10, rect.y + 50, rect.width - 20, 35),
                           prompt="", font_size=18, max_len=50)
    name_input.text = room.nombre
    name_input.active = True

    desc_input = TextInput((rect.x + 10, rect.y + 120, rect.width - 20, 80),
                           prompt="", font_size=16, max_len=500)
    desc_input.text = room.descripcion
    desc_input.active = False

    done = False
    clock = pygame.time.Clock()

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_RETURN:
                    done = True
                if event.key == pygame.K_TAB:
                    name_input.active = not name_input.active
                    desc_input.active = not desc_input.active

            name_input.handle_event(event)
            desc_input.handle_event(event)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(screen, GOLD, rect, 2, border_radius=8)
        draw_text(screen, f"EDITAR HABITACIÓN #{room.numero}",
                  rect.x + 10, rect.y + 10, 18, GOLD, bold=True)
        draw_text(screen, "Nombre:", rect.x + 10, rect.y + 35, 14, WHITE)
        name_input.draw(screen)
        draw_text(screen, "Descripción (máx 500 caracteres):",
                  rect.x + 10, rect.y + 100, 14, WHITE)
        desc_input.draw(screen)
        draw_text(screen, "TAB: cambiar campo | ENTER: guardar | ESC: cancelar",
                  rect.x + 10, rect.y + 215, 12, MID_GRAY)
        pygame.display.flip()
        clock.tick(30)

    room.nombre = name_input.text.strip() or f"Habitación {room.numero}"
    room.descripcion = desc_input.text.strip()
    return True


def _ask_new_salida(screen, room, dungeon):
    """Wizard para añadir una nueva salida."""
    disponibles = [d for d in DIRECTIONS if room.salida_en(d) is None]

    if not disponibles:
        MessageDialog(
            screen, "Esta habitación ya tiene todas las salidas posibles (7).").run()
        return None

    questions = [
        {"key": "direccion", "prompt": "Dirección de la nueva salida:",
            "type": "choice", "choices": disponibles},
        {"key": "estado_hacia", "prompt": "Estado hacia el destino (¿puede pasar el grupo?):",
         "type": "choice", "choices": ["abierta", "cerrada"], "default": "abierta"},
        {"key": "estado_desde", "prompt": "Estado desde el destino (¿pueden volver?):",
         "type": "choice", "choices": ["abierta", "cerrada"], "default": "abierta"}
    ]

    text_zone = pygame.Rect(50, screen.get_height() -
                            200, screen.get_width() - 100, 180)
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

    direccion = wiz.answers.get("direccion")
    if not direccion:
        return None

    dx, dy, dz = DIR_DELTA.get(direccion, (0, 0, 0))
    dest_x = room.x + dx
    dest_y = room.y + dy
    dest_z = room.z + dz

    dest_room = dungeon.room_en(dest_x, dest_y, dest_z)

    if dest_room is None:
        dest_room = Room()
        dest_room.numero = dungeon.next_room_num()
        dest_room.x, dest_room.y, dest_room.z = dest_x, dest_y, dest_z
        dest_room.nombre = f"Habitación {dest_room.numero}"
        dungeon.rooms.append(dest_room)
        MessageDialog(
            screen, f"Se ha creado una nueva habitación en {direccion}.").run()

    salida = Salida(
        direccion=direccion,
        room_destino_id=dest_room.id,
        estado_hacia_destino=wiz.answers.get("estado_hacia", "abierta"),
        estado_hacia_origen=wiz.answers.get("estado_desde", "abierta")
    )
    room.salidas.append(salida)

    salida_inv = Salida(
        direccion=OPPOSITE[direccion],
        room_destino_id=room.id,
        estado_hacia_destino=wiz.answers.get("estado_desde", "abierta"),
        estado_hacia_origen=wiz.answers.get("estado_hacia", "abierta")
    )
    dest_room.salidas.append(salida_inv)

    return salida


def _ask_room_elements(screen, room, dungeon):
    """Wizard para configurar items, monstruos, PNJs y mecanismos."""
    W, H = screen.get_width(), screen.get_height()

    questions = [
        {"key": "n_items",
            "prompt": "Número de items (0-3):", "type": "int", "min": 0, "max": 3, "default": 0},
        {"key": "n_monstruos",
            "prompt": "Número de monstruos (0-3):", "type": "int", "min": 0, "max": 3, "default": 0},
        {"key": "n_pnjs",
            "prompt": "Número de PNJs (0-3):", "type": "int", "min": 0, "max": 3, "default": 0},
        {"key": "n_mecanismos",
            "prompt": "Número de mecanismos (0-3):", "type": "int", "min": 0, "max": 3, "default": 0}
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

    room.items = []
    room.monstruos = []
    room.pnjs = []
    room.mecanismos = []

    for i in range(wiz.answers.get("n_items", 0)):
        elemento = _pick_or_create_element(
            screen, dungeon, dungeon.items_globales, "item")
        if elemento:
            room.items.append(elemento)

    for i in range(wiz.answers.get("n_monstruos", 0)):
        elemento = _pick_or_create_element(
            screen, dungeon, dungeon.monstruos_globales, "monstruo")
        if elemento:
            room.monstruos.append(elemento)

    for i in range(wiz.answers.get("n_pnjs", 0)):
        elemento = _pick_or_create_element(
            screen, dungeon, dungeon.pnjs_globales, "pnj")
        if elemento:
            room.pnjs.append(elemento)

    for i in range(wiz.answers.get("n_mecanismos", 0)):
        elemento = _pick_or_create_element(
            screen, dungeon, dungeon.mecanismos_globales, "mecanismo", room.salidas)
        if elemento:
            room.mecanismos.append(elemento)

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

    btn_edit_room = Button((elements_rect.x + 10, elements_rect.y + 60, elem_w - 20, 35),
                           "✏ Editar Habitación", font_size=12)
    btn_add_exit = Button((elements_rect.x + 10, elements_rect.y + 100, elem_w - 20, 35),
                          "🚪 Añadir Salida", font_size=12)
    btn_delete_room = Button((elements_rect.x + 10, elements_rect.y + 140, elem_w - 20, 35),
                             "🗑 Eliminar Habitación", font_size=12, color=C_ERROR)
    btn_elements = Button((elements_rect.x + 10, elements_rect.y + 180, elem_w - 20, 35),
                          "⚙ Configurar Elementos", font_size=12)

    help_lines = [
        "EDITOR DE DUNGEON",
        "Click izquierdo: seleccionar habitación",
        "Click derecho: centrar mapa",
        "Rueda ratón: scroll | ESC: guardar y salir"
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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if btn_z_up.rect.collidepoint(mx, my):
                    z_level += 1
                    selected_room_id = None
                elif btn_z_down.rect.collidepoint(mx, my):
                    z_level -= 1
                    selected_room_id = None
                elif btn_z_reset.rect.collidepoint(mx, my):
                    z_level = 0
                    selected_room_id = None

            if event.type == pygame.MOUSEMOTION and dragging:
                mx, my = pygame.mouse.get_pos()
                dx = (mx - drag_start[0]) // CELL_PX
                dy = (my - drag_start[1]) // CELL_PX
                offset_x = drag_offset[0] + dx
                offset_y = drag_offset[1] - dy

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if map_rect.collidepoint(mx, my):
                    clicked_room = None
                    for room in dungeon.rooms:
                        if room.z != z_level:
                            continue
                        cx, cy = _map_to_screen(
                            room.x, room.y, map_rect, offset_x, offset_y)
                        rr = pygame.Rect(
                            cx - ROOM_SIZE // 2, cy - ROOM_SIZE // 2, ROOM_SIZE, ROOM_SIZE)
                        if rr.collidepoint(mx, my):
                            clicked_room = room
                            break
                    if clicked_room:
                        selected_room_id = clicked_room.id
                    else:
                        selected_room_id = None
                elif elements_rect.collidepoint(mx, my):
                    if btn_edit_room.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                _ask_room_editor(screen, room)
                    elif btn_add_exit.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room:
                                _ask_new_salida(screen, room, dungeon)
                    elif btn_delete_room.handle_event(event):
                        if selected_room_id:
                            room = dungeon.room_por_id(selected_room_id)
                            if room and len(dungeon.rooms) > 1:
                                if ConfirmDialog(screen, f"¿Eliminar habitación '{room.nombre}'?").run():
                                    for r in dungeon.rooms:
                                        for s in r.salidas[:]:
                                            if s.room_destino_id == room.id:
                                                r.salidas.remove(s)
                                    dungeon.rooms.remove(room)
                                    selected_room_id = None
                            elif len(dungeon.rooms) <= 1:
                                MessageDialog(
                                    screen, "No se puede eliminar la última habitación.").run()
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

        screen.fill(BLACK)

        # Dibujar mapa
        pygame.draw.rect(screen, BG_MAP, map_rect)
        pygame.draw.rect(screen, MID_GRAY, map_rect, 1)

        rooms_z = [r for r in dungeon.rooms if r.z == z_level]
        for room in rooms_z:
            cx, cy = _map_to_screen(
                room.x, room.y, map_rect, offset_x, offset_y)
            for salida in room.salidas:
                if salida.direccion in ("arriba", "abajo", "especial"):
                    continue
                dest = dungeon.room_por_id(salida.room_destino_id)
                if dest and dest.z == z_level:
                    dx, dy = _map_to_screen(
                        dest.x, dest.y, map_rect, offset_x, offset_y)
                    color = GREEN if salida.estado_hacia_destino == "abierta" else RED
                    pygame.draw.line(screen, color, (cx, cy), (dx, dy), 2)

        for room in rooms_z:
            cx, cy = _map_to_screen(
                room.x, room.y, map_rect, offset_x, offset_y)
            rr = pygame.Rect(cx - ROOM_SIZE // 2, cy -
                             ROOM_SIZE // 2, ROOM_SIZE, ROOM_SIZE)

            if not map_rect.colliderect(rr.inflate(20, 20)):
                continue

            fill = (80, 80, 100) if room.id == selected_room_id else ROOM_FILL
            pygame.draw.rect(screen, fill, rr)
            pygame.draw.rect(screen, ROOM_BORDER, rr, 2)
            font = get_font(10)
            ns = font.render(str(room.numero), True, YELLOW)
            screen.blit(ns, (rr.x + 2, rr.y + 2))
            name_s = font.render(room.nombre[:10], True, LIGHT_GRAY)
            screen.blit(name_s, (rr.x + 2, rr.y + 14))

        # Dibujar controles Z
        btn_z_up.draw(screen)
        btn_z_down.draw(screen)
        btn_z_reset.draw(screen)

        # Mostrar nivel Z actual
        z_text = get_font(12).render(f"Nivel Z: {z_level}", True, GOLD)
        screen.blit(z_text, (map_rect.right - 80, map_rect.bottom - 25))

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
                draw_text(
                    screen, f"Coord: ({room.x}, {room.y}, {room.z})", elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(
                    screen, f"Salidas: {len(room.salidas)}/7", elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen, f"Items: {len(room.items)} | Monstruos: {len(room.monstruos)}",
                          elements_rect.x + 8, y, 11, WHITE)
                y += 15
                draw_text(screen, f"PNJs: {len(room.pnjs)} | Mecanismos: {len(room.mecanismos)}",
                          elements_rect.x + 8, y, 11, WHITE)

                btn_edit_room.rect.y = elements_rect.y + 140
                btn_add_exit.rect.y = elements_rect.y + 180
                btn_delete_room.rect.y = elements_rect.y + 220
                btn_elements.rect.y = elements_rect.y + 260

                btn_edit_room.draw(screen)
                btn_add_exit.draw(screen)
                btn_delete_room.draw(screen)
                btn_elements.draw(screen)
        else:
            draw_text(screen, "Selecciona una habitación",
                      elements_rect.x + 8, elements_rect.y + 60, 12, MID_GRAY)

        # Zona de texto
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

    persistence.guardar_dungeon(dungeon)
    return dungeon
