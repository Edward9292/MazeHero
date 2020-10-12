from __future__ import annotations
import pygame
from typing import Optional
from settings import *

class Actor:

    x: int
    y: int
    icon: pygame.Surface

    def __init__(self, icon_file, x, y):

        self.x, self.y = x, y
        self.icon = pygame.image.load(icon_file)

    def move(self, game: 'Game') -> None:
        raise NotImplementedError


class Player(Actor):

    x: int
    y: int
    icon: pygame.Surface
    _stars_collected: int
    _last_event: Optional[int]
    _smooth_move: bool

    def __init__(self, icon_file: str, x: int, y: int) -> None:

        super().__init__(icon_file, x, y)
        self._stars_collected = 0
        self._last_event = None # This is used for precise movement
        self._smooth_move = False # Turn this on for smooth movement

    def set_smooth_move(self, status: bool) -> None:
        self._smooth_move = status

    def get_star_count(self) -> int:
        return self._stars_collected

    def register_event(self, event: int) -> None:
        self._last_event = event

    def move(self, game: 'Game') -> None:
        evt = self._last_event

        if self._last_event:
            dx, dy = 0, 0
            if self._smooth_move: # Smooth movement used by the ghost level

                if game.keys_pressed[pygame.K_LEFT] or game.keys_pressed[
                    pygame.K_a]:
                    dx -= 1
                elif game.keys_pressed[pygame.K_RIGHT] or game.keys_pressed[
                    pygame.K_d]:
                    dx += 1
                elif game.keys_pressed[pygame.K_UP] or game.keys_pressed[
                    pygame.K_w]:
                    dy -= 1
                elif game.keys_pressed[pygame.K_DOWN] or game.keys_pressed[
                    pygame.K_s]:
                    dy += 1

            else: # Precise movement used by the squishy monster level
                if evt == pygame.K_LEFT or evt == pygame.K_a:
                    dx -= 1
                if evt == pygame.K_RIGHT or evt == pygame.K_d:
                    dx += 1
                if evt == pygame.K_UP or evt == pygame.K_w:
                    dy -= 1
                if evt == pygame.K_DOWN or evt == pygame.K_s:
                    dy += 1
                self._last_event = None

            new_x, new_y = self.x + dx, self.y + dy


            actor = game.get_actor(new_x, new_y)
            if isinstance(actor, Wall):
                return None
            if isinstance(actor, Star):
                game.remove_actor(actor)
                self._stars_collected += 1
            if isinstance(actor, Box):
                if not actor.be_pushed(game, dx, dy):
                    return None
            if isinstance(actor, Portal):
                actor.player_in(self)
                return None
            self.x, self.y = new_x, new_y
            if game.able_to_shoot:
                bullet = Bullet("../images/bullet-24.png", self.x, self.y,)
                game.add_actor(bullet)
                bullet.shoot(dx, dy)


class Star(Actor):

    x: int
    y: int
    icon: pygame.Surface

    def move(self, game: 'Game') -> None:
        pass


class Wall(Actor):

    x: int
    y: int
    icon: pygame.Surface

    def move(self, game: 'Game') -> None:
        pass


class Box(Actor):

    x: int
    y: int
    icon: pygame.Surface

    def move(self, game: 'Game') -> None:
        pass


    def be_pushed(self, game: 'Game', dx: int, dy: int) -> bool:

        new_x = self.x + dx
        new_y = self.y + dy
        actor = game.get_actor(new_x, new_y)
        if not isinstance(actor, Actor):
            self.x, self.y = new_x, new_y
            return True
        else:
            if isinstance(actor, Wall):
                return False
            elif isinstance(actor, SquishyMonster):
                actor.die(game)
                self.x, self.y = new_x, new_y
                return True
            elif isinstance(actor, Box):
                if actor.be_pushed(game, dx, dy):
                    self.x, self.y = new_x, new_y
                    return True
                else:
                    return False


    # === Classes for monsters === #
class Monster(Actor):

    x: int
    y: int
    icon: pygame.Surface
    _dx: float
    _dy: float
    _delay: int
    _delay_count: int

    def __init__(self, icon_file: str, x: int, y: int, dx: float, dy: float) -> None:
        super().__init__(icon_file, x, y)
        self._dx = dx
        self._dy = dy
        self._delay = 5
        self._delay_count = 1

    def move(self, game: 'Game') -> None:
        raise NotImplementedError

    def check_player_death(self, game: 'Game') -> None:
        if game.player.x == self.x and game.player.y == self.y:
            game.game_over()


class GhostMonster(Monster):

    x: int
    y: int
    icon: pygame.Surface
    _dx: float
    _dy: float
    _delay: int
    _delay_count: int

    def __init__(self, icon_file: str, x: int, y: int) -> None:

        super().__init__(icon_file, x, y, 0.5, 0.5)

    def move(self, game: 'Game') -> None:

        if game.player.x > self.x:
            self.x += self._dx
        elif game.player.x < self.x:
            self.x -= self._dx
        elif game.player.y > self.y:
            self.y += self._dy
        elif game.player.y < self.y:
            self.y -= self._dy

        self.check_player_death(game)


class SquishyMonster(Monster):

    x: int
    y: int
    icon: pygame.Surface
    _dx: float
    _dy: float
    _delay: int
    _delay_count: int

    def __init__(self, icon_file: str, x: int, y: int) -> None:

        super().__init__(icon_file, x, y, 1, 1)

    def move(self, game: 'Game') -> None:

        if self._delay_count == 0:
            x = self.x + self._dx
            y = self.y + self._dy
            x2 = self.x - self._dx
            y2 = self.y - self._dy
            actor = game.get_actor(x,y)
            actor2 = game.get_actor(x2, y2)
            if isinstance(actor, Box) or isinstance(actor, Wall):
                if isinstance(actor2, Box) or isinstance(actor2, Wall):

                    self._delay_count = (self._delay_count + 1) % self._delay
                    self.check_player_death(game)
                    return None

                self._dx = -1 * self._dx
                self._dy = -1 * self._dy
            self.x += self._dx
            self.y += self._dy

        self._delay_count = (self._delay_count + 1) % self._delay

        self.check_player_death(game)

    def die(self, game: 'Game') -> None:

        game.monster_count -= 1
        game.remove_actor(self)


class Door(Actor):

    x: int
    y: int
    icon: pygame.Surface

    def move(self, game: 'Game'):
        pass


class Portal(Actor):

    x: int
    y: int
    icon: pygame.Surface
    partner: Portal

    def __init__(self, icon_file, x, y):

        super().__init__(icon_file, x, y)
        self.partner = None


    def move(self, game: 'Game'):
        pass

    def set_partner(self, partner: Portal):
        self.partner = partner

    def player_in(self, actor: Actor):
        actor.x, actor.y = self.partner.x, self.partner.y

class Bullet(Actor):

    x: int
    y: int
    icon: pygame.Surface
    _dx: int
    _dy: int

    def move(self, game: 'Game'):
        new_x = self.x + self._dx
        new_y = self.y + self._dy
        actor = game.get_actor(self.x, self.y)
        actor2 = game.get_actor(self.x - self._dx, self.y - self._dy)
        actor3 = game.get_actor(new_x, new_y)
        if isinstance(actor, Wall) or isinstance(actor, Door):
            game.remove_actor(self)
        elif isinstance(actor, Monster):
            game.remove_actor(actor)
            game.ghost_count -= 1
            game.remove_actor(self)
        elif isinstance(actor2, Monster):  # Prevent monster pass through bullet
            game.remove_actor(actor2)
            game.ghost_count -= 1
            game.remove_actor(self)
        elif isinstance(actor3, Monster):  # Prevent monster pass through bullet
            game.remove_actor(actor3)
            game.ghost_count -= 1
            game.remove_actor(self)
        self.x, self.y = new_x, new_y

    def shoot(self, dx, dy):
        self._dx = dx
        self._dy = dy
