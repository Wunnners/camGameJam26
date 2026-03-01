import heapq
import math

import pygame

from enemy import Enemy, Health, move_with_collision
from game_config import TILE_SIZE
from ss import *
from animation import *


def _world_to_tile(point):
    return point[0] // TILE_SIZE, point[1] // TILE_SIZE


def _tile_center(tile):
    return (
        tile[0] * TILE_SIZE + TILE_SIZE // 2,
        tile[1] * TILE_SIZE + TILE_SIZE // 2,
    )


def _rect_to_tiles(rect):
    left = rect.left // TILE_SIZE
    right = (rect.right - 1) // TILE_SIZE
    top = rect.top // TILE_SIZE
    bottom = (rect.bottom - 1) // TILE_SIZE

    covered_tiles = set()
    for tile_y in range(top, bottom + 1):
        for tile_x in range(left, right + 1):
            covered_tiles.add((tile_x, tile_y))
    return covered_tiles


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _find_path(start, goal, blocked_tiles, width, height):
    if start == goal:
        return [start]

    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {}
    g_score = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            return _reconstruct_path(came_from, current)

        for delta_x, delta_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (current[0] + delta_x, current[1] + delta_y)
            if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                continue
            if neighbor in blocked_tiles and neighbor != goal:
                continue

            tentative_cost = g_score[current] + 1
            if tentative_cost >= g_score.get(neighbor, float("inf")):
                continue

            came_from[neighbor] = current
            g_score[neighbor] = tentative_cost
            priority = tentative_cost + _heuristic(neighbor, goal)
            heapq.heappush(frontier, (priority, neighbor))

    return [start]


class Basic(Enemy):
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 35, 35)
        self.speed = 2
        self.color = (255, 50, 50)
        self.attack_damage = 10
        self.attack_cooldown = 2000
        self.last_attack_time = 0
        self.health = Health(50, self.rect)

        self.path = []
        self.path_refresh_ms = 250
        self.last_path_update = -100000
        self.last_goal_tile = None
        self.last_start_tile = None
        self.stuck_frames = 0

        # sps = Spritesheet('assets/bh/Ninja Adventure - Asset Pack/Actor/Animals/Cat/Faceset.png', 32)
        sps = Spritesheet('assets/bh/Ninja Adventure - Asset Pack/Actor/Characters/Cavegirl/SpriteSheet.png', 16)
        self.a = (Animation(sps, 5, [0]),)

    def is_active(self):
        return self.health.current_hp <= 0
    
    def take_damage(self, amount):
        self.health.take_damage(amount)

    def _build_blocked_tiles(self, nav_data):
        level_rows = nav_data["level_map"]
        blocked_tiles = set()

        for tile_y, row in enumerate(level_rows):
            for tile_x, char in enumerate(row):
                if char in {"W", "B"}:
                    blocked_tiles.add((tile_x, tile_y))

        for door in nav_data.get("doors", []):
            if not door.is_open:
                blocked_tiles.update(_rect_to_tiles(door.rect))

        for gate in nav_data.get("gates", []):
            if not gate.is_open:
                blocked_tiles.update(_rect_to_tiles(gate.rect))

        return blocked_tiles, len(level_rows[0]), len(level_rows)

    def _refresh_path(self, player, nav_data):
        blocked_tiles, map_width, map_height = self._build_blocked_tiles(nav_data)
        start_tile = _world_to_tile(self.rect.center)
        goal_tile = _world_to_tile(player.rect.center)

        blocked_tiles.discard(start_tile)
        blocked_tiles.discard(goal_tile)

        self.path = _find_path(start_tile, goal_tile, blocked_tiles, map_width, map_height)
        self.last_path_update = pygame.time.get_ticks()
        self.last_start_tile = start_tile
        self.last_goal_tile = goal_tile

    def _move_along_path(self, player, nav_data):
        now = pygame.time.get_ticks()
        current_tile = _world_to_tile(self.rect.center)
        goal_tile = _world_to_tile(player.rect.center)

        should_refresh = (
            not self.path
            or now - self.last_path_update >= self.path_refresh_ms
            or current_tile != self.last_start_tile
            or goal_tile != self.last_goal_tile
            or self.stuck_frames >= 8
        )
        if should_refresh:
            self._refresh_path(player, nav_data)
            self.stuck_frames = 0

        while len(self.path) > 1 and self.path[0] != current_tile:
            self.path.pop(0)

        if not self.path:
            self.path = [current_tile]

        next_tile = self.path[1] if len(self.path) > 1 else goal_tile
        target_x, target_y = _tile_center(next_tile)
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery

        tile_step_x = next_tile[0] - current_tile[0]
        tile_step_y = next_tile[1] - current_tile[1]

        # Follow the path one grid step at a time:
        # align on the perpendicular axis first, then advance through the corridor.
        if tile_step_x != 0:
            if abs(dy) > 2:
                dx = 0
            else:
                dy = 0
        elif tile_step_y != 0:
            if abs(dx) > 2:
                dy = 0
            else:
                dx = 0

        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        vx = (dx / dist) * self.speed
        vy = (dy / dist) * self.speed

        obstacles = list(nav_data.get("boundaries", []))
        obstacles.extend(door.rect for door in nav_data.get("doors", []) if not door.is_open)
        obstacles.extend(gate.rect for gate in nav_data.get("gates", []) if not gate.is_open)
        previous_position = self.rect.topleft
        move_with_collision(self.rect, vx, vy, obstacles)
        if self.rect.topleft == previous_position:
            self.stuck_frames += 1
        else:
            self.stuck_frames = 0

    def _move_direct(self, player, obstacles):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist != 0 and dist < 400:
            vx = (dx / dist) * self.speed
            vy = (dy / dist) * self.speed
            move_with_collision(self.rect, vx, vy, obstacles)

    def update(self, player, nav_or_obstacles):
        if isinstance(nav_or_obstacles, dict):
            self._move_along_path(player, nav_or_obstacles)
        else:
            self._move_direct(player, nav_or_obstacles)

        if self.rect.colliderect(player.rect):
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > self.attack_cooldown:
                player.take_damage(self.attack_damage)
                self.last_attack_time = current_time

    def draw(self, surface, camera):
        # pygame.draw.rect(surface, self.color, camera.apply(self.rect))
        bruh = camera.apply(self.rect)
        img = self.a[0].get_image()
        # surface.blit(img, (bruh.x, bruh.y))
        surface.blit(pygame.transform.scale(img, bruh.size), (bruh.x, bruh.y))
        self.health.draw(surface, camera)
