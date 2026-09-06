import time
from typing import Self

import pygame as pg

from modules.level import Boid
from modules.level import Level


class Game(object):

    _SCREEN_SIZE = (640, 480)
    _SURF_RATIO = (2, 2)
    _SURF_SIZE = (int(_SCREEN_SIZE[0] / _SURF_RATIO[0]),
                  int(_SCREEN_SIZE[1] / _SURF_RATIO[1]))
    _SCREEN_FLAGS = pg.RESIZABLE | pg.SCALED
    _GAME_SPEED = 5
    _TIMESTEP = 1 / 30

    def __init__(self: Self) -> None:
        pg.init()

        self._settings = {
            'vsync': 1,
        }
        self._screen = pg.display.set_mode(
            self._SCREEN_SIZE,
            flags=self._SCREEN_FLAGS,
            vsync=self._settings['vsync']
        )
        pg.display.set_caption('Boidstacle')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        
        rect = self._surface.get_rect()
        self._obstacles = []
        self._boids = Level(
            Level.random_boids(100, pos_range=rect, bound=rect),
            self._obstacles,
        )

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        accumulator = 0

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()
            
            rel_game_speed = delta_time * self._GAME_SPEED

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.MOUSEBUTTONDOWN:
                    rect = pg.Rect(0, 0, 32, 32)
                    rect.center = pg.Vector2(event.pos) / 2
                    self._obstacles.append(rect)

            # Update
            self._boids.update(rel_game_speed)

            # Render
            self._surface.fill((0, 0, 0))
            for y in range(self._SURF_SIZE[1] // 16):
                for x in range(self._SURF_SIZE[0] // 16):
                    pos = pg.Vector2(x, y) * 16
                    self._surface.set_at(pos, (255, 255, 255))
            for obstacle in self._obstacles:
                pg.draw.rect(self._surface, (0, 255, 0), obstacle)
            self._boids.render(self._surface, accumulator / self._TIMESTEP)
            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

