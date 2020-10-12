from __future__ import annotations
from typing import Optional, List
from actors import *
import pygame
import random

LEVEL_MAPS = ["maze1.txt", "maze3.txt", "maze2.txt"]

def load_map(filename: str) -> List[List[str]]:
    with open(filename) as f:
        map_data = [line.split() for line in f]
    return map_data

class Game:

    def __init__(self) -> None:

        self._running = False
        self._level = 0 # Current level that the game is in
        self._max_level = len(LEVEL_MAPS)-1
        self.screen = None
        self.player = None
        self.keys_pressed = None

        # Attributes that get set during level setup
        self._actors = None
        self.stage_width, self.stage_height = 0, 0
        self.size = None
        self.goal_message = None
        self.door = None

        # Attributes that are specific to certain levels
        self.goal_stars = 0  # Level 0
        self.monster_count = 0  # Level 1
        self.ghost_count = 0  # Level 2
        self.able_to_shoot = False # Level 2

        # Method that takes care of level setup
        self.setup_current_level()


    def get_level(self) -> int:
        return self._level

    def set_player(self, player: Player) -> None:
        self.player = player

    def add_actor(self, actor: Actor) -> None:
        self._actors.append(actor)

    def remove_actor(self, actor: Actor) -> None:
        self._actors.remove(actor)

    def get_actor(self, x: int, y: int) -> Optional[Actor]:

        for actor in self._actors:
            if actor.x == x and actor.y == y:
                return actor

    def on_init(self) -> None:

        pygame.init()
        self.screen = pygame.display.set_mode \
            (self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True

    def on_event(self, event: pygame.Event) -> None:

        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            self.player.register_event(event.key)

    def game_won(self) -> bool:

        if self.player.x == self.door.x and self.player.y == self.door.y:
            if self.get_level() == 0:
                return self.player.get_star_count() >= self.goal_stars
            elif self.get_level() == 1:
                return self.monster_count == 0
            elif self.get_level() == 2:
                return self.ghost_count == 0

        return False

    def on_loop(self) -> None:

        self.keys_pressed = pygame.key.get_pressed()
        for actor in self._actors:
            actor.move(self)
        if self.player is None:
            print("You lose! :( Better luck next time.")
            self._running = False
        elif self.game_won():
            if not self._level == self._max_level:
                self._level += 1
                self.setup_current_level()
            else:
                print("Congratulations, you won!")
                self._running = False

    def on_render(self) -> None:

        self.screen.fill(BLACK)
        for a in self._actors:
            rect = pygame.Rect(a.x * ICON_SIZE, a.y * ICON_SIZE, ICON_SIZE, ICON_SIZE)
            self.screen.blit(a.icon, rect)

        font = pygame.font.Font('freesansbold.ttf', 12)
        text = font.render(self.goal_message, True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.center = (self.stage_width * ICON_SIZE // 2, \
                           (self.stage_height + 0.5) * ICON_SIZE)
        self.screen.blit(text, textRect)

        pygame.display.flip()

    def on_cleanup(self) -> None:
        pygame.quit()

    def on_execute(self) -> None:
        self.on_init()

        while self._running:
            pygame.time.wait(100)
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()

    def game_over(self) -> None:
        self.player = None

    def setup_current_level(self):
        data = load_map(
            "../data/"+LEVEL_MAPS[self._level])  # Set the file where maze data is stored

        if self._level == 0:
            self.setup_ghost_game(data)
        elif self._level == 1:
            self.setup_squishy_monster_game(data)
        elif self._level == 2:
            self.setup_adventurer_game(data)

    def setup_ghost_game(self, data) -> None:

        w = len(data[0])
        h = len(
            data) + 1  # We add a bit of space for the text at the bottom

        self._actors = []
        self.stage_width, self.stage_height = w, h-1
        self.size = (w * ICON_SIZE, h * ICON_SIZE)

        player, chaser = None, None

        for i in range(len(data)):
            for j in range(len(data[i])):
                key = data[i][j]
                if key == 'P':
                    player = Player("../images/boy-24.png", j, i)
                elif key == 'C':
                    chaser = GhostMonster("../images/ghost-24.png", j, i)
                elif key == 'X':
                    self.add_actor(Wall("../images/wall-24.png", j, i))
                elif key == 'D':
                    self.add_actor(Door("../images/door-24.png", j, i))
                    self.door = self.get_actor(j, i)

        self.set_player(player)
        self.add_actor(player)
        player.set_smooth_move(True) # Enable smooth movement for player
        self.add_actor(chaser)
        # Set the number of stars the player must collect to win
        self.goal_stars = 5
        self.goal_message = "Objective: Collect {}".format(self.goal_stars) + \
                           " stars before the ghost gets you and head for the door"

        # Draw stars
        num_stars = 0
        while num_stars < 7:
            x = random.randrange(self.stage_width)
            y = random.randrange(self.stage_height)
            actor = self.get_actor(x, y)
            if not isinstance(actor, Actor):
                self.add_actor(Star("../images/star-24.png", x, y))
                num_stars += 1


    def setup_squishy_monster_game(self, data) -> None:

        w = len(data[0])
        h = len(
            data) + 1  # We add a bit of space for the text at the bottom

        self._actors = []
        self.stage_width, self.stage_height = w, h-1
        self.size = (w * ICON_SIZE, h * ICON_SIZE)
        self.goal_message = "Objective: Squish all the monsters with the boxes " \
                           + " and head for the door"

        player, monster = None, None

        for i in range(len(data)):
            for j in range(len(data[i])):
                key = data[i][j]
                if key == 'P':
                    player = Player("../images/boy-24.png", j, i)
                elif key == 'M':
                    self.add_actor(SquishyMonster("../images/monster-24.png", j, i))
                    self.monster_count += 1
                elif key == 'X':
                    self.add_actor(Wall("../images/wall-24.png", j, i))
                elif key == 'D':
                    self.add_actor(Door("../images/door-24.png", j, i))
                    self.door = self.get_actor(j, i)

        self.set_player(player)
        self.add_actor(player)
        player.set_smooth_move(False)
        num_boxs = 0
        while num_boxs < 12:
            x = random.randrange(self.stage_width)
            y = random.randrange(self.stage_height)
            actor = self.get_actor(x, y)
            if not isinstance(actor, Actor):
                self.add_actor(Box("../images/box-24.png", x, y))
                num_boxs += 1


    def setup_adventurer_game(self, data) -> None:

        w = len(data[0])
        h = len(
            data) + 1  # We add a bit of space for the text at the bottom

        self._actors = []
        self.stage_width, self.stage_height = w, h-1
        self.size = (w * ICON_SIZE, h * ICON_SIZE)
        self.goal_message = "Objective: Kill all the Ghosts by bullet " \
                           + " and head for the door"

        player, chaser = None, None

        for i in range(len(data)):
            for j in range(len(data[i])):
                key = data[i][j]
                if key == 'P':
                    player = Player("../images/boy-24.png", j, i)
                elif key == 'M':
                    self.add_actor(GhostMonster("../images/ghost-24.png", j, i))
                    self.ghost_count += 1
                elif key == 'X':
                    self.add_actor(Wall("../images/wall-24.png", j, i))
                elif key == 'D':
                    self.add_actor(Door("../images/door-24.png", j, i))
                    self.door = self.get_actor(j, i)

        self.set_player(player)
        self.add_actor(player)
        player.set_smooth_move(False)
        self.able_to_shoot = True  # Able to shoot the bullet

        num_portal = 0
        portals = []
        while num_portal < 2:
            x = random.randrange(self.stage_width)
            y = random.randrange(self.stage_height)

            actor = self.get_actor(x, y)
            if not isinstance(actor, Actor):
                self.add_actor(Portal("../images/portal-24.png", x, y))
                portals.append(self.get_actor(x, y))
                num_portal += 1
        portals[0].partner = portals[1]
        portals[1].partner = portals[0]

