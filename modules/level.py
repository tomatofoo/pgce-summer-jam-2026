from __future__ import annotations

import math
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
                 vis_radius: Real=32,
                 fov: Real=270,
                 separation: Real=0.05,
                 alignment: Real=0.05,
                 cohesion: Real=0.005,
                 speed_range: tuple[Real, Real]=(0, 70),
                 bound: pg.Rect=pg.Rect(0, 0, 0, 0),
                 rollover: pg.Rect=pg.Rect(0, 0, 0, 0)) -> None:
        self._pos = pg.Vector2(pos)
        self._last_pos = self._pos.copy()
        self._velocity = pg.Vector2(velocity)
        self._accel = pg.Vector2(0, 0)
        self._phys_radius = phys_radius
        self._vis_radius = vis_radius
        self._fov = fov
        self._separation = separation
        self._alignment = alignment
        self._cohesion = cohesion
        self._speed_range = speed_range
        self._bound = bound
        self._rollover = rollover

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

    def _offsets(self: Self) -> None:
        if self._pos[0] > self._rollover.centerx:
            if self._pos[1] > self._rollover.centery:
                return ((0, 0), (1, 0), (0, 1), (1, 1))
            return ((0, 0), (1, 0), (1, -1), (0, -1))
        elif self._pos[1] > self._rollover.centery:
            return ((0, 0), (-1, 0), (-1, 1), (0, 1))
        return ((0, 0), (-1, 0), (-1, -1), (0, -1))

    def _basic_update(self: Self, boids: list[Boid]) -> None:
        # Boids algorithm
        self._accel = pg.Vector2(0, 0)
        vel_avg = pg.Vector2(0, 0)
        pos_avg = pg.Vector2(0, 0)
        count = 0
        offsets = self._offsets()
        for boid in boids:
            if boid is self:
                continue
            boid_pos = boid._pos
            if self._rollover[2] and self._rollover[3]:
                lowest = math.inf
                for offset in offsets:
                    tentative = (
                        boid._pos
                        + (offset[0] * self._rollover[2],
                           offset[1] * self._rollover[3])
                    )
                    dist_sq = self._pos.distance_squared_to(tentative)
                    if dist_sq < lowest:
                        lowest = dist_sq
                        boid_pos = tentative
            rel = boid_pos - self._pos
            mag = rel.magnitude()
            if mag < self._vis_radius:
                if mag < self._phys_radius:
                    self._accel -= rel * self._separation
                if self._fov:
                    angle = rel.angle_to(self._velocity)
                    angle = min(angle, 360 - angle)
                if not self._fov or angle < self._fov * 0.5:
                    vel_avg += boid._velocity
                    pos_avg += boid_pos
                    count += 1
        if count:
            vel_avg /= count
            pos_avg /= count
            self._accel += (vel_avg - self._velocity) * self._alignment
            self._accel += (pos_avg - self._pos) * self._cohesion

    def update(self: Self,
               rel_game_speed: Real,
               boids: set[Boid],
               obstacles: list[pg.Rect]=[]) -> None:
        # Euler Integration
        self._basic_update(boids)
        self._velocity += self._accel * rel_game_speed
        if self._velocity:
            self._last_pos = self._pos.copy()
            self._velocity.clamp_magnitude(*self._speed_range)
            self._pos += self._velocity * rel_game_speed
        if self._rollover[2] and self._rollover[3]:
            rel = self._pos - self._last_pos
            self._pos[0] = (
                (self._pos[0] - self._rollover[0]) % self._rollover[2]
                + self._rollover[0]
            )
            self._pos[1] = (
                (self._pos[1] - self._rollover[1]) % self._rollover[3]
                + self._rollover[1]
            )
            self._last_pos = self._pos - rel

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
                 boids: list[Boid]=[],
                 obstacles: list[pg.Rect]=[],
                 timestep: Real=0.02) -> None:
        self._boids = boids
        self._obstacles = obstacles
        self._timestep = timestep
        self._accumulator = 0

    @staticmethod
    def random_boids(count: int,
                     pos_range: pg.Rect=pg.Rect(0, 0, 0, 0),
                     vel_range: pg.Rect=pg.Rect(-50, -50, 100, 100),
                     phys_radius: Real=8,
                     vis_radius: Real=64,
                     fov: Real=270,
                     separation: Real=2.5,
                     alignment: Real=2.5,
                     cohesion: Real=0.25,
                     speed_range: tuple[Real, Real]=(0, 70),
                     bound: pg.Rect=pg.Rect(0, 0, 0, 0),
                     rollover: pg.Rect=pg.Rect(0, 0, 0, 0)) -> set[Boid]:
        boids = []
        for i in range(count):
            boids.append(Boid(
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
                speed_range,
                bound,
                rollover,
            ))
        return boids

    @property
    def boids(self: Self) -> list[Boid]:
        return self._boids

    @boids.setter
    def boids(self: Self, value: list[Boid]) -> None:
        self._boids = value

    @property
    def obstacles(self: Self) -> list[pg.Rect]:
        return self._obstacles

    @obstacles.setter
    def obstacles(self: Self, value: list[pg.Rect]) -> None:
        self._obstacles = value

    @property
    def timestep(self: Self) -> Real:
        return self._timestep

    @timestep.setter
    def timestep(self: Self, value: Real) -> None:
        self._timestep = value

    def update(self: Self, rel_game_speed: Real) -> None:
        if self._timestep:
            self._accumulator += rel_game_speed
            while self._accumulator >= self._timestep:
                for boid in self._boids:
                    boid.update(self._timestep, self._boids, self._obstacles)
                self._accumulator -= self._timestep
        else:
            for boid in self._boids:
                boid.update(rel_game_speed, self._boids, self._obstacles)

    def render(self: Self, surf: pg.Surface) -> None:
        for boid in self._boids:
            boid.render(
                surf,
                self._accumulator / self._timestep if self._timestep else 1,
            )

