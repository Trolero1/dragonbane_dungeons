# screen_elementos.py - Pantalla de gestión de elementos globales

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, MessageDialog
import screen_dungeons


class ScreenElementos:
    """Pantalla de gestión de elementos globales (items, monstruos, PNJs, mecanismos)."""

    def __init__(self, app):
        self.app = app
        W = app.screen.get_width()

        btn_w, btn_h, gap = 200, 56, 24
        total_w = 5 * btn_w + 4 * gap
        start_x = W // 2 - total_w // 2

        self.btn_items = Button((start_x, 390, btn_w, btn_h),
                                "📦  ITEMS", font_size=16, bold=True,
                                color=(60, 100, 140))

        self.btn_monstruos = Button((start_x + btn_w + gap, 390, btn_w, btn_h),
                                    "👹  MONSTRUOS", font_size=16, bold=True,
                                    color=(140, 60, 60))

        self.btn_pnjs = Button((start_x + 2 * (btn_w + gap), 390, btn_w, btn_h),
                               "🧑  PNJS", font_size=16, bold=True,
                               color=(60, 120, 80))

        self.btn_mecanismos = Button((start_x + 3 * (btn_w + gap), 390, btn_w, btn_h),
                                     "⚙  MECANISMOS", font_size=16, bold=True,
                                     color=(140, 110, 40))

        self.btn_inicio = Button((start_x + 4 * (btn_w + gap), 390, btn_w, btn_h),
                                 "🏠  INICIO", font_size=16, bold=True,
                                 color=(80, 40, 40))

        self.buttons = [self.btn_items, self.btn_monstruos, self.btn_pnjs, self.btn_mecanismos, self.btn_inicio]

    def handle_event(self, event):
        if self.btn_inicio.handle_event(event):
            self.app.current_screen = screen_dungeons.ScreenDungeonsManager(self.app)
            return

        if self.btn_items.handle_event(event):
            MessageDialog(self.app.screen, "Gestión de items - Próximamente.").run()

        elif self.btn_monstruos.handle_event(event):
            MessageDialog(self.app.screen, "Gestión de monstruos - Próximamente.").run()

        elif self.btn_pnjs.handle_event(event):
            MessageDialog(self.app.screen, "Gestión de PNJs - Próximamente.").run()

        elif self.btn_mecanismos.handle_event(event):
            MessageDialog(self.app.screen, "Gestión de mecanismos - Próximamente.").run()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mp)

    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)

        W = surf.get_width()
        draw_text(surf, "EDITOR DE ELEMENTOS", W // 2 - 150, 190, 28, C_SUBTITULO, bold=True)
        draw_text(surf, "Crea, modifica o elimina items, monstruos, pnjs, mecanismos",
                  W // 2 - 280, 240, 14, C_TEXTO_DIM, max_width=560)

        for btn in self.buttons:
            btn.draw(surf)

    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "DRAGONBANE", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)
