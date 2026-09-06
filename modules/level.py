from __future__ import annotations

import random as rand
from numbers import Real
from typing import Self

import pygame as pg


# https://vanhunteradams.com/Pico/Animal_Movement/Boids-algorithm.html
class Boid(object):
    def __init__(self: Self,
                 pos: pg.Vector2,
                 velocity: pg.Vector2,
                 phys_radius: Real=8,
                 vis_radius: Real=64,
                 fov: Real=180,
                 separation: Real=0.05,
                 alignment: Real=0.05,
                 cohesion: Real=0.005,
                 bound: pg.Rect=pg.Rect(0, 0, 0, 0)) -> None:
        self._pos = pg.Vector2(pos)
        self._last_pos = self._pos.copy()
        self._velocity = pg.Vector2(velocity)
        self._phys_radius = phys_radius
        self._vis_radius = vis_radius
        self._fov = fov
        self._separation = separation
        self._alignment = alignment
        self._cohesion = cohesion
        self._bound = bound

    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos

    @pos.setter
    def pos(self: Self, value: pg.Vector2) -> None:
        self._pos = value

    @property
    def velocity(self: Self) -> pg.Vector2:
        return self._velocity

    @velocity.setter
    def velocity(self: Self, value: pg.Vector2) -> None:
        self._velocity = value

    @property
    def phys_radius(self: Self) -> Real:
        return self._phys_radius

    @phys_radius.setter
    def phys_radius(self: Self, value: Real) -> None:
        self._phys_radius = value

    @property
    def vis_radius(self: Self) -> Real:
        return self._vis_radius

    @vis_radius.setter
    def vis_radius(self: Self, value: Real) -> None:
        self._vis_radius = value

    @property
    def fov(self: Self) -> Real:
        return self._fov

    @fov.setter
    def fov(self: Self, value: Real) -> None:
        self._fov = value

    def update(self: Self,
               rel_game_speed: Real,
               boids: set[Boid],
               obstacles: list[pg.Rect]=[]) -> None:
        self._last_pos = self._pos.copy()

        # Boids algorithm
        vel_avg = pg.Vector2(0, 0)
        pos_avg = pg.Vector2(0, 0)
        count = 0
        for boid in boids:
            if boid is self:
                continue
            rel = boid._pos - self._pos
            mag = rel.magnitude()
            if mag < self._vis_radius:
                if mag < self._phys_radius:
                    self._velocity -= rel * self._separation
                if self._fov:
                    angle = rel.angle_to(self._velocity)
                    angle = min(angle, 360 - angle)
                if not self._fov or angle < self._fov * 0.5:
                    vel_avg += boid._velocity
                    pos_avg += boid._pos
                    count += 1
        if count:
            vel_avg /= count
            pos_avg /= count
            self._velocity += (vel_avg - self._velocity) * self._alignment
            self._velocity += (pos_avg - self._pos) * self._cohesion
        if self._bound:
            pass
        self._pos += self._velocity * rel_game_speed

    def render(self: Self, surf: pg.Surface, t: Real) -> None:
        pos = self._last_pos.lerp(self._pos, t)
        pg.draw.circle(surf, (255, 255, 255), pos, 2)
        if self._velocity:
            pg.draw.circle(
                surf,
                (255, 255, 255),
                pos + self._velocity.normalize() * 2,
                1,
            )


class Level(object):
    def __init__(self: Self,
                 boids: set[Boid]=set(),
                 obstacles: list[pg.Rect]=[]) -> None:
        self._boids = boids
        self._obstacles = obstacles
        self._sets = {}
        self._tilesize = 64

    @staticmethod
    def random_boids(count: int,
                     pos_range: pg.Rect=pg.Rect(0, 0, 0, 0),
                     vel_range: pg.Rect=pg.Rect(-50, -50, 100, 100),
                     phys_radius: Real=8,
                     vis_radius: Real=64,
                     fov: Real=180,
                     separation: Real=0.05,
                     alignment: Real=0.05,
                     cohesion: Real=0.005,
                     bound: pg.Rect=pg.Rect(0, 0, 0, 0)) -> set[Boid]:
        boids = set()
        for i in range(count):
            boids.add(Boid(
                (rand.randint(pos_range.left, pos_range.right),
                 rand.randint(pos_range.top, pos_range.bottom)),
                (rand.randint(vel_range.left, vel_range.right),
                 rand.randint(vel_range.top, vel_range.bottom)),
                phys_radius,
                vis_radius,
                fov,
                separation,
                alignment,
                cohesion,
                bound,
            ))
        return boids

    def _gen_key(self: Self, boid: Boid) -> None:
        return (
            boid._pos[0] // self._tilesize,
            boid._pos[1] // self._tilesize,
        )

    def _update_sets(self: Self) -> None:
        self._sets = {}
        for boid in self._boids:
            key = self._gen_key(boid)
            boids = self._sets.get(key)
            if boids is None:
                self._sets[key] = {boid}
            else:
                boids.add(boid)

    def update(self: Self, rel_game_speed: Real) -> None:
        # self._update_sets()
        for boid in self._boids:
            boid.update(rel_game_speed, self._boids, self._obstacles)

    def render(self: Self, surf: pg.Surface, t: Real=1) -> None:
        for boid in self._boids:
            boid.render(surf, t)

