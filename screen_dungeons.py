# screen_dungeons.py - Pantalla principal del Editor de Dungeons
#
# Botones: CREAR, MODIFICAR, ELIMINAR, SALIR

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, MessageDialog, ConfirmDialog, ScrollList, TextInput
import persistence
import screen_editor
from models import Dungeon
from datetime import datetime


class ScreenDungeonsManager:
    """Pantalla principal de gestión de dungeons."""
    
    def __init__(self, app):
        self.app = app
        W = app.screen.get_width()
        
        # 4 botones centrados
        btn_w, btn_h, gap = 200, 56, 24
        total_w = 4 * btn_w + 3 * gap
        start_x = W // 2 - total_w // 2
        
        self.btn_crear = Button((start_x, 390, btn_w, btn_h),
                                "🏰  CREAR", font_size=16, bold=True,
                                color=(106, 48, 16))
        
        self.btn_modificar = Button((start_x + btn_w + gap, 390, btn_w, btn_h),
                                    "✏  MODIFICAR", font_size=16, bold=True)
        
        self.btn_eliminar = Button((start_x + 2 * (btn_w + gap), 390, btn_w, btn_h),
                                   "🗑  ELIMINAR", font_size=16, bold=True,
                                   color=C_ERROR)
        
        self.btn_salir = Button((start_x + 3 * (btn_w + gap), 390, btn_w, btn_h),
                                "🚪  SALIR", font_size=16, bold=True,
                                color=(80, 40, 40))
        
        self.buttons = [self.btn_crear, self.btn_modificar, self.btn_eliminar, self.btn_salir]
    
    def handle_event(self, event):
        # Botón SALIR
        if self.btn_salir.handle_event(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        
        # Botón CREAR
        if self.btn_crear.handle_event(event):
            self._crear_dungeon()
        
        # Botón MODIFICAR
        elif self.btn_modificar.handle_event(event):
            self._modificar_dungeon()
        
        # Botón ELIMINAR
        elif self.btn_eliminar.handle_event(event):
            self._eliminar_dungeon()
    
    def _crear_dungeon(self):
        """Crea un nuevo dungeon."""
        nombre = self._ask_name("Nombre del nuevo Dungeon:")
        if not nombre:
            return
        
        dungeon = Dungeon()
        dungeon.numero = persistence.obtener_siguiente_numero_dungeon()
        dungeon.nombre = nombre
        dungeon.fecha_creacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        screen_editor.run_editor(self.app.screen, dungeon)
    
    def _modificar_dungeon(self):
        """Modifica un dungeon existente."""
        dungeons = persistence.listar_dungeons()
        if not dungeons:
            MessageDialog(self.app.screen, "No hay dungeons creados.").run()
            return
        
        idx = self._pick_dungeon(dungeons, "SELECCIONA DUNGEON A MODIFICAR")
        if idx is None:
            return
        
        dungeon = persistence.cargar_dungeon(dungeons[idx]["id"])
        screen_editor.run_editor(self.app.screen, dungeon)
    
    def _eliminar_dungeon(self):
        """Elimina un dungeon existente."""
        dungeons = persistence.listar_dungeons()
        
        if not dungeons:
            MessageDialog(self.app.screen, "No hay dungeons creados.").run()
            return
        
        idx = self._pick_dungeon(dungeons, "SELECCIONA DUNGEON A ELIMINAR")
        if idx is None:
            return
        
        d = dungeons[idx]
        if ConfirmDialog(self.app.screen, 
                         f"¿Eliminar dungeon '{d['nombre']}'? Esta acción no se puede deshacer.").run():
            persistence.eliminar_dungeon(d["id"])
            MessageDialog(self.app.screen, f"Dungeon '{d['nombre']}' eliminado.").run()
    
    def _pick_dungeon(self, dungeons, title):
        """Muestra lista de dungeons y devuelve índice."""
        W, H = self.app.screen.get_width(), self.app.screen.get_height()
        rect = pygame.Rect(W // 2 - 350, H // 2 - 200, 700, 400)
        
        labels = [f"#{d.get('numero', '?')}  {d['nombre']}  ({d['num_rooms']} rooms)  {d['fecha_creacion']}" 
              for d in dungeons]
        
        sl = ScrollList(rect, labels, font_size=14, title=title)
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                idx = sl.handle_event(event)
                if idx is not None:
                    return idx
            
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.app.screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(self.app.screen, DARK_GRAY, rect, border_radius=6)
            pygame.draw.rect(self.app.screen, GOLD, rect, 2, border_radius=6)
            sl.draw(self.app.screen)
            
            hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
            self.app.screen.blit(hint, (rect.x + 10, rect.bottom - 18))
            pygame.display.flip()
            clock.tick(30)
    
    def _ask_name(self, prompt):
        """Diálogo para pedir nombre."""
        W, H = self.app.screen.get_width(), self.app.screen.get_height()
        rect = pygame.Rect(W // 2 - 300, H // 2 - 40, 600, 80)
        
        inp = TextInput((rect.x + 10, rect.y + 40, rect.width - 20, 30),
                        prompt="", font_size=17)
        clock = pygame.time.Clock()
        
        while not inp.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                inp.handle_event(event)
            
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.app.screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(self.app.screen, DARK_GRAY, rect, border_radius=6)
            pygame.draw.rect(self.app.screen, GOLD, rect, 2, border_radius=6)
            draw_text(self.app.screen, prompt, rect.x + 10, rect.y + 10, 16, YELLOW, bold=True)
            inp.draw(self.app.screen)
            pygame.display.flip()
            clock.tick(30)
        
        return inp.text.strip() or None
    
    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mp)
    
    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)
        
        W = surf.get_width()
        draw_text(surf, "EDITOR DE DUNGEONS", W // 2 - 150, 190, 28, C_SUBTITULO, bold=True)
        draw_text(surf, "Crea nuevos calabozos, modifica los existentes o elimínalos",
                  W // 2 - 280, 240, 14, C_TEXTO_DIM, max_width=560)
        
        for btn in self.buttons:
            btn.draw(surf)
    
    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "DRAGONBANE", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)