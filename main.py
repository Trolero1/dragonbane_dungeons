#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRAGONBANE - Editor de Dungeons
Programa para crear, modificar y eliminar dungeons para el juego Dragonbane.
"""

import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import SCREEN_W, SCREEN_H, TITLE, FPS
from screen_dungeons import ScreenDungeonsManager


class DragonbaneEditor:
    """Clase principal del editor de dungeons."""
    
    def __init__(self):
        pygame.init()
        pygame.freetype.init()
        
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE + " - Editor de Dungeons")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Pantalla actual (solo gestión de dungeons)
        self.current_screen = ScreenDungeonsManager(self)
        
    def run(self):
        """Bucle principal del editor."""
        while self.running:
            dt = self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                else:
                    self.current_screen.handle_event(event)
            
            self.current_screen.update(dt)
            self.current_screen.draw(self.screen)
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    editor = DragonbaneEditor()
    editor.run()