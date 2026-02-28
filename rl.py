import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pygame


class WorldEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    window_size = 800
    scale = window_size // 20

    def __init__(self, render_mode="human"):
        super().__init__()
        self.render_mode = render_mode
        self.window = None

        # ===== Environment Parameters =====
        self.arena_size = 10.0
        self.max_health = 15
        self.attack_range = 1.5
        self.attack_angle_tolerance = np.pi / 6
        self.attack_cooldown_time = 0.5
        self.dt = 1 / 60

        self.accel = 0.6

        # ===== Action Space =====
        # move_x, move_y, aim_accel, attack
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -np.pi / 69, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0, np.pi / 69, 1.0], dtype=np.float32),
        )

        # ===== Observation Space =====
        # dx, dy, self_cd, enemy_cd, self_hp, enemy_hp
        high = np.array(
            [self.arena_size * 2, # posx
             self.arena_size * 2, # posy
             1.0, # vx
             1.0, # vy
             1.0, # cos ang
             1.0, # sin ang
             1.0, # ang vel
             10.0, # p1 cd
             10.0, # p2 cd
             self.max_health,
             self.max_health],
            dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-high,
            high=high,
            dtype=np.float32
        )

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.p1_pos = np.random.uniform(-2, 2, size=2)
        self.p2_pos = np.random.uniform(-2, 2, size=2)

        self.p1_vel = [0, 0]
        self.p2_vel = [0, 0]

        self.aim_angle = 0
        self.angle_vel = 0

        self.attack = False

        self.p1_health = self.max_health
        self.p2_health = self.max_health

        self.p1_cd = 0.0
        self.p2_cd = 0.0

        self.t = 0

        return self._get_obs(), {}

    def _get_obs(self):
        dx = self.p2_pos[0] - self.p1_pos[0]
        dy = self.p2_pos[1] - self.p1_pos[1]

        return np.array([
            dx,
            dy,
            self.p1_vel[0],
            self.p1_vel[1],
            np.cos(self.aim_angle),
            np.sin(self.aim_angle),
            self.angle_vel,
            self.p1_cd,
            self.p2_cd,
            self.p1_health,
            self.p2_health
        ], dtype=np.float32)

    def step(self, action):
        move_x, move_y, aim_diff, attack = action
        self.angle_vel += aim_diff
        self.angle_vel *= 0.81
        self.aim_angle += self.angle_vel
        self.attack = False

        reward = 0.0
        terminated = False
        truncated = False

        # ===== Movement =====
        move_vec = np.array([move_x, move_y])
        # reward += (move_x ** 1 + move_y ** 1) * 0.1
        # move_vec = np.array([1, 0])
        norm = np.linalg.norm(move_vec)
        if norm > 1:
            move_vec = move_vec / norm

        self.p1_vel += move_vec * self.accel * self.dt
        self.p1_vel *= 0.91

        self.p1_pos += self.p1_vel
        # Clamp to arena
        self.p1_pos = np.clip(self.p1_pos, -self.arena_size, self.arena_size)

        # ===== Enemy Simple Policy (Random) =====
        enemy_move = np.random.uniform(-1, 1, size=2)
        enemy_norm = np.linalg.norm(enemy_move)
        if enemy_norm > 1:
            enemy_move /= enemy_norm

        self.p2_vel += enemy_move * self.accel * self.dt
        self.p2_vel *= 0.91

        self.p2_pos += self.p2_vel
        # Clamp to arena
        self.p2_pos = np.clip(self.p2_pos, -self.arena_size, self.arena_size)

        # ===== Cooldowns =====
        self.p1_cd = max(0.0, self.p1_cd - self.dt)
        self.p2_cd = max(0.0, self.p2_cd - self.dt)

        # ===== Player Attack =====
        dx = self.p2_pos[0] - self.p1_pos[0]
        dy = self.p2_pos[1] - self.p1_pos[1]
        distance = np.sqrt(dx**2 + dy**2)
        angle_to_enemy = np.arctan2(dy, dx)

        if attack > 0 and self.p1_cd == 0:
            miss = True
            self.attack = True
            if distance < self.attack_range:
                angle_diff = np.abs(self._angle_diff(self.aim_angle, angle_to_enemy))
                if angle_diff < self.attack_angle_tolerance:
                    self.p2_health -= 1
                    reward += 0.1
                    miss = False
                    self.p2_vel += np.array([dx, dy]) / distance * 0.3
            if miss:
                reward -= 0.05
            self.p1_cd = self.attack_cooldown_time

        # ===== Enemy Random Attack =====
        # if self.p2_cd == 0 and distance < self.attack_range:
        #     if np.random.rand() < 0.1:
        #         self.p1_health -= 
        #         reward -= 0.1
        #         self.p2_cd = self.attack_cooldown_time

        # ===== Distance Penalty =====
        reward -= 0.001 * distance

        # ===== Win/Loss =====
        if self.p2_health <= 0:
            reward += 1.0
            terminated = True

        if self.p1_health <= 0:
            reward -= 1.0
            terminated = True

        self.t += 1
        if self.t > 500:
            truncated = True

        return self._get_obs(), reward, terminated, truncated, {}

    def _angle_diff(self, a, b):
        diff = a - b
        return (diff + np.pi) % (2 * np.pi) - np.pi
    
    def render(self):
        if self.window is None:
            pygame.init()
            self.window = pygame.display.set_mode((self.window_size, self.window_size))
            pygame.display.set_caption("1v1 Melee RL")
            self.clock = pygame.time.Clock()

        self.window.fill((30, 30, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.window = None
                return

        # Convert world -> screen
        def to_screen(pos):
            return (
                int((pos[0] + self.arena_size) * self.scale),
                int((pos[1] + self.arena_size) * self.scale),
            )

        p1_screen = to_screen(self.p1_pos)
        p2_screen = to_screen(self.p2_pos)

        # Draw players
        pygame.draw.circle(self.window, (50, 150, 255), p1_screen, 12)
        pygame.draw.circle(self.window, (255, 80, 80), p2_screen, 12)

        # attacks
        dx = np.cos(self.aim_angle)
        dy = np.sin(self.aim_angle)
        if self.attack:
            pygame.draw.circle(self.window, (0, 255, 0), (p1_screen[0] + int(dx * 25), p1_screen[1] + int(dy * 25)), 10)

        # Draw attack direction
        end_x = p1_screen[0] + int(dx * 25)
        end_y = p1_screen[1] + int(dy * 25)
        pygame.draw.line(self.window, (255, 255, 0), p1_screen, (end_x, end_y), 3)

        # Health bars
        pygame.draw.rect(self.window, (0, 0, 255), (20, 20, 20 * self.p1_health, 10)) # blue
        pygame.draw.rect(self.window, (255, 0, 0), (20, 40, 20 * self.p2_health, 10)) # red

        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        if self.window is not None:
            pygame.quit()
            self.window = None



if __name__ == "__main__":
    env = WorldEnv(render_mode="human")
    obs, _ = env.reset()

    for _ in range(1000):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            obs, _ = env.reset()
        env.render()

    env.close()