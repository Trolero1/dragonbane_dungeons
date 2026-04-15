# ui_utils.py - Utilidades de interfaz de usuario para DUNGUEONS (Pygame)
#
# Este archivo contiene todos los componentes reutilizables de la interfaz gráfica:
# funciones para dibujar texto, y clases que representan widgets interactivos
# como campos de texto, listas con scroll, diálogos de confirmación y el sistema
# de preguntas secuenciales (wizard).
#
# La idea es que los archivos de pantalla (screen_menu.py, screen_editor.py,
# screen_game.py) no tengan que preocuparse por los detalles de cómo se dibuja
# un botón o cómo se valida una respuesta numérica. Importan estas utilidades
# y las usan como piezas prefabricadas.
#
# Este tipo de organización se llama "separación de responsabilidades":
# ui_utils.py sabe cómo DIBUJAR componentes de interfaz,
# los archivos de pantalla saben qué MOSTRAR y qué HACER con las respuestas.


# Importamos pygame, la librería gráfica principal del juego.
import pygame
# "from constants import *" importa TODOS los nombres definidos en constants.py
# directamente al espacio de nombres de este archivo. Así podemos escribir WHITE
# en vez de constants.WHITE, BLACK en vez de constants.BLACK, etc.
# El asterisco * es una "importación comodín". En general se desaconseja porque
# puede causar confusión sobre de dónde viene cada nombre, pero cuando se importa
# un archivo de constantes que se usa intensivamente en todo el código, como aquí,
# es una excepción aceptada porque hace el código mucho más limpio.
from constants import *


# ══════════════════════════════════════════════════════════════════════════════
# CACHÉ DE FUENTES
# ══════════════════════════════════════════════════════════════════════════════
# _fonts es un diccionario que actúa como caché de fuentes ya cargadas.
# La clave es una tupla (tamaño, bold) y el valor es el objeto fuente de Pygame.
# El guión bajo indica que es una variable privada de este módulo.
#
# ¿Por qué una caché? Cargar una fuente desde el sistema operativo con
# pygame.font.SysFont() es una operación relativamente costosa en tiempo.
# Si la llamáramos cada vez que queremos dibujar texto, el programa sería
# notablemente más lento. Con la caché, cada combinación (tamaño, bold)
# se carga solo la primera vez y se reutiliza en todas las llamadas siguientes.
_fonts = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("monospace", size, bold=bold)
    return _fonts[key]


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN draw_text
# ══════════════════════════════════════════════════════════════════════════════

def draw_text(surf, text, x, y, size=16, color=WHITE, bold=False, max_width=None):
    font = get_font(size, bold)
    
    if max_width:
        words = text.split(" ")
        lines, line = [], ""
        for w in words:
            test = (line + " " + w).strip()
            if font.size(test)[0] <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        for i, l in enumerate(lines):
            s = font.render(l, True, color)
            surf.blit(s, (x, y + i * (size + 2)))
        return len(lines) * (size + 2)
    else:
        s = font.render(text, True, color)
        surf.blit(s, (x, y))
        return size + 2


# ══════════════════════════════════════════════════════════════════════════════
# CLASE Button
# ══════════════════════════════════════════════════════════════════════════════

class Button:
    def __init__(self, rect, text, font_size=15, bold=True,
                 color=C_BOTON, color_hover=C_BOTON_HOV,
                 color_sel=C_BOTON_SEL, color_text=C_BOTON_TXT,
                 selected=False, disabled=False, wrap=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font_size = font_size
        self.bold = bold
        self.color = color
        self.color_hover = color_hover
        self.color_sel = color_sel
        self.color_text = color_text
        self.selected = selected
        self.disabled = disabled
        self.wrap = wrap
        self.hovered = False
    
    def draw(self, surf, offset_y=0):
        r = self.rect.move(0, -offset_y)
        if not (-self.rect.height < r.y < surf.get_height() + self.rect.height):
            return
        if self.disabled:
            bg = tuple(max(0, c - 40) for c in self.color)
            txt_col = C_TEXTO_DIM
        elif self.selected:
            bg = self.color_sel
            txt_col = (20, 10, 5)
        elif self.hovered:
            bg = self.color_hover
            txt_col = self.color_text
        else:
            bg = self.color
            txt_col = self.color_text
        
        pygame.draw.rect(surf, bg, r, border_radius=6)
        pygame.draw.rect(surf, C_BORDE, r, 2, border_radius=6)
        
        font = get_font(self.font_size, bold=self.bold)
        tw, th = font.size(self.text)
        s = font.render(self.text, True, txt_col)
        surf.blit(s, (r.x + (r.width - tw) // 2, r.y + (r.height - th) // 2))
    
    def handle_event(self, event, offset_y=0):
        r = self.rect.move(0, -offset_y)
        if event.type == pygame.MOUSEMOTION:
            self.hovered = r.collidepoint(event.pos) and not self.disabled
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.collidepoint(event.pos) and not self.disabled:
                return True
        return False
    
    def update_hover(self, mouse_pos, offset_y=0):
        r = self.rect.move(0, -offset_y)
        self.hovered = r.collidepoint(mouse_pos) and not self.disabled


# ══════════════════════════════════════════════════════════════════════════════
# CLASE TextInput
# ══════════════════════════════════════════════════════════════════════════════

class TextInput:
    def __init__(self, rect, prompt="", max_len=80, font_size=16, color_active=YELLOW, center=False, active=True):
        self.rect = pygame.Rect(rect)
        self.prompt = prompt
        self.max_len = max_len
        self.font_size = font_size
        self.color_active = color_active
        self.center = center
        self.text = ""
        self.active = active          # ← Ahora usa el parámetro
        self.done = False
        self.cursor_timer = 0
        self.cursor_visible = True
    
    def handle_event(self, event, offset_y=0):
        if not self.active:
            return
        r = self.rect.move(0, -offset_y)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.done = True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_len and event.unicode.isprintable():
                    self.text += event.unicode
        # Activar con clic
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.collidepoint(event.pos):
                self.active = True
    
    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer > 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surf, offset_y=0):
        r = self.rect.move(0, -offset_y)
        font = get_font(self.font_size)
        
        pygame.draw.rect(surf, DARK_GRAY, r)
        pygame.draw.rect(surf, self.color_active if self.active else MID_GRAY, r, 2)
        
        prompt_surf = font.render(self.prompt, True, MID_GRAY)
        surf.blit(prompt_surf, (r.x + 4, r.y + 4))
        
        px = r.x + 4 + prompt_surf.get_width() + 6
        display_text = self.text + ("_" if self.active and self.cursor_visible else "")
        text_surf = font.render(display_text, True, WHITE)
        surf.blit(text_surf, (px, r.y + 4))


# ══════════════════════════════════════════════════════════════════════════════
# CLASE ScrollArea
# ══════════════════════════════════════════════════════════════════════════════

class ScrollArea:
    def __init__(self):
        self.offset = 0
        self.max_offset = 0
        self.scroll_speed = 30
    
    def reset(self):
        self.offset = 0
        self.max_offset = 0
    
    def set_content_height(self, content_h, view_h):
        self.max_offset = max(0, content_h - view_h + 60)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.offset -= event.y * self.scroll_speed
            self.offset = max(0, min(self.offset, self.max_offset))
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.offset = min(self.offset + self.scroll_speed, self.max_offset)
            if event.key == pygame.K_UP:
                self.offset = max(self.offset - self.scroll_speed, 0)
            if event.key == pygame.K_PAGEDOWN:
                self.offset = min(self.offset + 400, self.max_offset)
            if event.key == pygame.K_PAGEUP:
                self.offset = max(self.offset - 400, 0)
    
    def draw_scrollbar(self, surf, view_rect):
        if self.max_offset <= 0:
            return
        total = self.max_offset + view_rect.height
        bar_h = max(40, int(view_rect.height * view_rect.height / total))
        bar_y = view_rect.y + int(self.offset / total * view_rect.height)
        sb_rect = pygame.Rect(view_rect.right - 10, bar_y, 8, bar_h)
        pygame.draw.rect(surf, C_BORDE, sb_rect, border_radius=4)


# ══════════════════════════════════════════════════════════════════════════════
# CLASE ScrollList
# ══════════════════════════════════════════════════════════════════════════════

class ScrollList:
    def __init__(self, rect, items, font_size=16, title="", selectable=True):
        self.rect = pygame.Rect(rect)
        self.items = items
        self.font_size = font_size
        self.title = title
        self.selectable = selectable
        self.scroll = 0
        self.selected = None
        self.line_h = font_size + 6
    
    def max_visible(self):
        return max(1, (self.rect.height - 30) // self.line_h)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if not self.rect.collidepoint(mx, my):
                return None
            if event.button == 4:
                self.scroll = max(0, self.scroll - 1)
            elif event.button == 5:
                self.scroll = min(max(0, len(self.items) - self.max_visible()), self.scroll + 1)
            elif event.button == 1 and self.selectable:
                rel_y = my - self.rect.y - 28
                idx = self.scroll + rel_y // self.line_h
                if 0 <= idx < len(self.items):
                    self.selected = idx
                    return idx
        return None
    
    def draw(self, surf):
        pygame.draw.rect(surf, BG_PANEL, self.rect)
        pygame.draw.rect(surf, MID_GRAY, self.rect, 1)
        
        font = get_font(self.font_size)
        if self.title:
            t = get_font(self.font_size, bold=True).render(self.title, True, GOLD)
            surf.blit(t, (self.rect.centerx - t.get_width() // 2, self.rect.y + 6))
        
        visible = self.items[self.scroll:self.scroll + self.max_visible()]
        for i, item in enumerate(visible):
            abs_i = self.scroll + i
            y = self.rect.y + 28 + i * self.line_h
            if abs_i == self.selected:
                pygame.draw.rect(surf, DARK_GRAY, (self.rect.x + 2, y, self.rect.width - 4, self.line_h))
            color = YELLOW if abs_i == self.selected else WHITE
            txt = font.render(str(item), True, color)
            surf.blit(txt, (self.rect.x + 6, y + 2))
        
        total = len(self.items)
        if total > self.max_visible():
            hint = get_font(12).render(
                f"↑↓ scroll  {self.scroll+1}-{min(self.scroll+self.max_visible(), total)}/{total}",
                True, MID_GRAY)
            surf.blit(hint, (self.rect.x + 4, self.rect.bottom - 16))


# ══════════════════════════════════════════════════════════════════════════════
# CLASE Checkbox
# ══════════════════════════════════════════════════════════════════════════════

class Checkbox:
    def __init__(self, x, y, text, font_size=13, checked=False, disabled=False, max_label_w=200):
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.checked = checked
        self.disabled = disabled
        self.max_label_w = max_label_w
        self.box_size = 18
        self.hovered = False
    
    def _rect(self, offset_y=0):
        return pygame.Rect(self.x, self.y - offset_y, self.box_size, self.box_size)
    
    def draw(self, surf, offset_y=0):
        br = self._rect(offset_y)
        if self.disabled:
            border_col = C_TEXTO_DIM
            check_col = C_TEXTO_DIM
            txt_col = C_TEXTO_DIM
            bg = C_FONDO
        elif self.checked:
            border_col = C_TITULO
            check_col = C_TITULO
            txt_col = C_SUBTITULO
            bg = C_ENTRADA_SEL
        elif self.hovered:
            border_col = C_BOTON_HOV
            check_col = C_BOTON_HOV
            txt_col = C_TEXTO
            bg = C_ENTRADA
        else:
            border_col = C_BORDE
            check_col = C_TITULO
            txt_col = C_TEXTO
            bg = C_FONDO
        
        pygame.draw.rect(surf, bg, br, border_radius=3)
        pygame.draw.rect(surf, border_col, br, 2, border_radius=3)
        
        if self.checked:
            cx, cy = br.x + self.box_size // 2, br.y + self.box_size // 2
            pygame.draw.line(surf, check_col, (br.x + 3, cy), (cx - 1, br.y + self.box_size - 4), 2)
            pygame.draw.line(surf, check_col, (cx - 1, br.y + self.box_size - 4), (br.x + self.box_size - 3, br.y + 4), 2)
        
        draw_text(surf, self.text, br.x + self.box_size + 6, br.y, self.font_size, txt_col, max_width=self.max_label_w)
    
    def handle_event(self, event, offset_y=0):
        br = self._rect(offset_y)
        font = get_font(self.font_size)
        label_w = min(font.size(self.text)[0], self.max_label_w)
        full_rect = pygame.Rect(br.x, br.y, self.box_size + 6 + label_w, max(self.box_size, 30))
        if event.type == pygame.MOUSEMOTION:
            self.hovered = full_rect.collidepoint(event.pos) and not self.disabled
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if full_rect.collidepoint(event.pos) and not self.disabled:
                self.checked = not self.checked
                return True
        return False
    
    def update_hover(self, mouse_pos, offset_y=0):
        br = self._rect(offset_y)
        full_rect = pygame.Rect(br.x, br.y, self.box_size + 200, self.box_size)
        self.hovered = full_rect.collidepoint(mouse_pos) and not self.disabled


# ══════════════════════════════════════════════════════════════════════════════
# CLASE ConfirmDialog
# ══════════════════════════════════════════════════════════════════════════════

class ConfirmDialog:
    def __init__(self, screen, message):
        self.screen = screen
        self.message = message
        self.result = None
        w, h = 480, 160
        sw, sh = screen.get_size()
        self.rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
    
    def run(self):
        clock = pygame.time.Clock()
        btn_yes = pygame.Rect(self.rect.x + 60, self.rect.bottom - 50, 140, 36)
        btn_no = pygame.Rect(self.rect.x + 280, self.rect.bottom - 50, 140, 36)
        
        while self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_yes.collidepoint(event.pos):
                        self.result = True
                    if btn_no.collidepoint(event.pos):
                        self.result = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.result = True
                    if event.key == pygame.K_ESCAPE:
                        self.result = False
            
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, DARK_GRAY, self.rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, self.rect, 2, border_radius=8)
            draw_text(self.screen, self.message, self.rect.x + 20, self.rect.y + 30, 16, WHITE, max_width=self.rect.width - 40)
            for btn, lbl, col in [(btn_yes, "  SÍ", GREEN), (btn_no, "  NO", RED)]:
                pygame.draw.rect(self.screen, col, btn, border_radius=4)
                draw_text(self.screen, lbl, btn.x + 10, btn.y + 8, 18, BLACK, bold=True)
            pygame.display.flip()
            clock.tick(30)
        return self.result


# ══════════════════════════════════════════════════════════════════════════════
# CLASE MessageDialog
# ══════════════════════════════════════════════════════════════════════════════

class MessageDialog:
    def __init__(self, screen, message, title="AVISO"):
        self.screen = screen
        self.message = message
        self.title = title
    
    def run(self):
        clock = pygame.time.Clock()
        w, h = 500, 200
        sw, sh = self.screen.get_size()
        rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        btn = pygame.Rect(rect.centerx - 60, rect.bottom - 50, 120, 36)
        done = False
        
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.collidepoint(event.pos):
                        done = True
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        done = True
            
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, DARK_GRAY, rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, rect, 2, border_radius=8)
            draw_text(self.screen, self.title, rect.x + 10, rect.y + 10, 18, GOLD, bold=True)
            draw_text(self.screen, self.message, rect.x + 20, rect.y + 45, 15, WHITE, max_width=rect.width - 40)
            pygame.draw.rect(self.screen, MID_GRAY, btn, border_radius=4)
            draw_text(self.screen, "  OK", btn.x + 10, btn.y + 8, 18, WHITE, bold=True)
            pygame.display.flip()
            clock.tick(30)


# ══════════════════════════════════════════════════════════════════════════════
# CLASE QuestionWizard (simplificada)
# ══════════════════════════════════════════════════════════════════════════════

class QuestionWizard:
    def __init__(self, screen, text_zone_rect, questions):
        self.screen = screen
        self.zone = pygame.Rect(text_zone_rect)
        self.questions = questions
        self.answers = {}
        self.current = 0
        self.input = None
        self.error_msg = ""
        self._build_input()
    
    def _build_input(self):
        if self.current >= len(self.questions):
            self.input = None
            return
        q = self.questions[self.current]
        input_rect = (self.zone.x + 10, self.zone.y + 60, self.zone.width - 20, 30)
        max_len = q.get("max_len", 80)
        self.input = TextInput(input_rect, prompt="→ ", font_size=15, max_len=max_len)
        self.error_msg = ""
    
    def handle_event(self, event):
        if self.input:
            self.input.handle_event(event)
            if self.input.done:
                self._validate()
    
    def _validate(self):
        q = self.questions[self.current]
        raw = self.input.text.strip()
        if not raw and "default" in q:
            raw = str(q["default"])
        t = q.get("type", "text")
        
        if t == "int":
            try:
                v = int(raw)
                mn = q.get("min", -9999)
                mx = q.get("max", 9999)
                if not (mn <= v <= mx):
                    self.error_msg = f"Introduce un número entre {mn} y {mx}"
                    self.input.text = ""
                    self.input.done = False
                    return
                self.answers[q["key"]] = v
            except ValueError:
                self.error_msg = "Introduce un número válido"
                self.input.text = ""
                self.input.done = False
                return
        elif t == "choice":
            choices = q.get("choices", [])
            low = raw.lower()
            match = None
            for c in choices:
                if c.lower().startswith(low) or c.lower() == low:
                    match = c
                    break
            if match is None:
                try:
                    idx = int(raw) - 1
                    if 0 <= idx < len(choices):
                        match = choices[idx]
                except ValueError:
                    pass
            if match is None:
                self.error_msg = f"Elige una opción válida: {', '.join(choices)}"
                self.input.text = ""
                self.input.done = False
                return
            self.answers[q["key"]] = match
        else:
            if not raw:
                self.error_msg = "Este campo no puede estar vacío"
                self.input.text = ""
                self.input.done = False
                return
            self.answers[q["key"]] = raw
        
        self.current += 1
        self._build_input()
    
    @property
    def finished(self):
        return self.current >= len(self.questions)
    
    def draw(self):
        pygame.draw.rect(self.screen, BG_TEXT, self.zone)
        pygame.draw.rect(self.screen, MID_GRAY, self.zone, 1)
        if self.current >= len(self.questions):
            return
        q = self.questions[self.current]
        font_sm = get_font(13)
        start = max(0, self.current - 3)
        for i, qi in enumerate(self.questions[start:self.current]):
            ans = self.answers.get(qi["key"], "")
            txt = font_sm.render(f"  {qi['prompt']}  →  {ans}", True, MID_GRAY)
            self.screen.blit(txt, (self.zone.x + 10, self.zone.y + 6 + i * 16))
        prompt_y = self.zone.y + 10 + min(3, self.current) * 16
        prompt_txt = q.get("prompt", "")
        if q.get("type") == "choice":
            choices = q.get("choices", [])
            prompt_txt += "  [" + " / ".join(f"{i+1}.{c}" for i, c in enumerate(choices)) + "]"
        draw_text(self.screen, prompt_txt, self.zone.x + 10, prompt_y, 15, YELLOW, max_width=self.zone.width - 20)
        if self.error_msg:
            draw_text(self.screen, "⚠ " + self.error_msg, self.zone.x + 10, prompt_y + 20, 13, RED)
        if self.input:
            self.input.rect.y = prompt_y + 38
            self.input.draw(self.screen)
# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN draw_rect_border
# ══════════════════════════════════════════════════════════════════════════════

def draw_rect_border(surf, rect, color, width=1):
    """Dibuja un rectángulo con borde (relleno transparente)."""
    pygame.draw.rect(surf, color, rect, width)



