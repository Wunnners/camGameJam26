import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pygame


class Player:
    def __init__(self):
        self.pos = np.random.uniform(-3, 3, size=2)
        self.vel = np.array([0, 0], dtype=float)
        self.angle = np.random.uniform(-np.pi, np.pi)
        self.angle_vel = 0
        self.attack = False
        self.health = 15
        self.cd = 0
        self.radius = 0.6


class WorldEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    window_size = 800
    player_speed = 1

    def __init__(self, render_mode="human"):
        super().__init__()
        self.render_mode = render_mode
        self.window = None

        # ===== Environment Parameters =====
        self.arena_size = 10.0
        self.scale = self.window_size // (self.arena_size * 2)
        self.max_health = 15
        self.attack_range = 2.0
        self.attack_angle_tolerance = np.pi / 6
        self.max_cd = 0.5
        self.dt = 1 / 60

        self.accel = 0.6
        self.ang_accel = np.pi / 69

        # ===== Action Space =====
        # move_x, move_y, aim_accel, attack
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -self.ang_accel, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0, self.ang_accel, 1.0], dtype=np.float32),
        )

        # ===== Observation Space =====
        # dx, dy, self_cd, enemy_cd, self_hp, enemy_hp
        high = np.array(
            [self.arena_size, # posx
             self.arena_size, # posy
             1.0, # vx
             1.0, # vy
             1.0, # cos ang
             1.0, # sin ang
             1.0, # ang vel
             0.5, # p1 cd
             0.5, # p2 cd
             self.max_health,
             self.max_health],
            dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-high,
            high=high,
            dtype=np.float32
        )

        self.p: list[Player] = None

        self.player_action = [0, 0, 0, 0]

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.p: list[Player] = [Player() for _ in range(2)]
        self.t = 0
        return (self._get_obs(0), {}), (self._get_obs(1), {})

    def _get_obs(self, idx=0):
        dx = self.p[idx^1].pos[0] - self.p[idx].pos[0]
        dy = self.p[idx^1].pos[1] - self.p[idx].pos[1]

        return np.array([
            dx,
            dy,
            self.p[idx].vel[0],
            self.p[idx].vel[1],
            np.cos(self.p[idx].angle),
            np.sin(self.p[idx].angle),
            self.p[idx].angle_vel,
            self.p[idx].cd,
            self.p[idx^1].cd,
            self.p[idx].health,
            self.p[idx^1].health
        ], dtype=np.float32)
    
    def update_player(self, idx, action):
        move_x, move_y, aim_diff, attack = action

        self.p[idx].angle_vel += aim_diff
        self.p[idx].angle_vel *= 0.81
        self.p[idx].angle += self.p[idx].angle_vel
        self.p[idx].attack = False

        reward = [0.0, 0.0]
        terminated = False
        truncated = False

        # ===== Movement =====
        move_vec = np.array([move_x, move_y])
        # move_vec = np.array([1, 0])
        norm = np.linalg.norm(move_vec)
        if norm > 1:
            move_vec = move_vec / norm

        self.p[idx].vel += move_vec * self.accel * self.dt
        self.p[idx].vel *= 0.91

        self.p[idx].pos += self.p[idx].vel
        # Clamp to arena
        self.p[idx].pos = np.clip(self.p[idx].pos, -self.arena_size, self.arena_size)

        # ===== Cooldowns =====
        self.p[idx].cd = max(0.0, self.p[idx].cd - self.dt)

        # ===== Player Attack =====
        dx = self.p[idx^1].pos[0] - self.p[idx].pos[0]
        dy = self.p[idx^1].pos[1] - self.p[idx].pos[1]
        distance = np.sqrt(dx**2 + dy**2)
        angle_to_enemy = np.arctan2(dy, dx)

        if attack > 0 and self.p[idx].cd == 0:
            miss = True
            self.p[idx].attack = True
            if distance < self.attack_range:
                angle_diff = np.abs(self._angle_diff(self.p[idx].angle, angle_to_enemy))
                if angle_diff < self.attack_angle_tolerance:
                    self.p[idx^1].health -= 1
                    reward[idx] += 0.1
                    reward[idx^1] -= 0.1
                    miss = False
                    self.p[idx^1].vel += np.array([dx, dy]) / distance * 0.3
            if miss:
                reward[idx] -= 0.02
            self.p[idx].cd = self.max_cd

        # ===== Distance Penalty =====
        reward[idx] -= 0.001 * distance

        # ===== Win/Loss =====
        if self.p[idx^1].health <= 0:
            reward[idx] += 1.0
            reward[idx^1] -= 1.0
            terminated = True

        return self._get_obs(idx), reward, terminated, truncated, {}

    def step(self, idx, action0, action1):
        obs0, reward0, terminated0, truncated, info = self.update_player(0, action0)
        obs1, reward1, terminated1, truncated, info  = self.update_player(1, action1)
        obs = [obs0, obs1]
        reward = [reward0[0] + reward1[0], reward0[1] + reward1[1]]

        self.resolve_collision(self.p[0], self.p[1])
        self.t += 1
        if self.t > 500:
            truncated = True
        terminated = terminated0 or terminated1
        return obs, reward, terminated, truncated, info

    def resolve_collision(self, p1: Player, p2: Player):
        dx = p2.pos[0] - p1.pos[0]
        dy = p2.pos[1] - p1.pos[1]
        dist = np.hypot(dx, dy)
        min_dist = p1.radius + p2.radius

        if dist < min_dist and dist != 0:  # collision detected
            # How much they overlap
            overlap = min_dist - dist

            # Normalize vector between centers
            nx = dx / dist
            ny = dy / dist

            # Push each player half the overlap away
            p1.pos[0] -= nx * overlap / 2
            p1.pos[1] -= ny * overlap / 2
            p2.pos[0] += nx * overlap / 2
            p2.pos[1] += ny * overlap / 2

    def _angle_diff(self, a, b):
        diff = a - b
        return (diff + np.pi) % (2 * np.pi) - np.pi
    
    def to_screen(self, pos):
        return (
            int((pos[0] + self.arena_size) * self.scale),
            int((pos[1] + self.arena_size) * self.scale),
        )

    def render(self):
        if self.window is None:
            pygame.init()
            self.window = pygame.display.set_mode((self.window_size, self.window_size))
            pygame.display.set_caption("1v1 Melee RL")
            self.clock = pygame.time.Clock()

        self.window.fill((30, 30, 30))

        left_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.window = None
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    left_clicked = True
        
        if self.render_mode == "human":
            keys = pygame.key.get_pressed()
            dx = 0
            dy = 0
            if keys[pygame.K_w]:
                dy -= self.player_speed
            if keys[pygame.K_s]:
                dy += self.player_speed
            if keys[pygame.K_a]:
                dx -= self.player_speed
            if keys[pygame.K_d]:
                dx += self.player_speed
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            center_x, center_y = self.to_screen(self.p[1].pos)
            angle = np.arctan2(mouse_y - center_y, mouse_x - center_x)
            angle_diff = self._angle_diff(angle, self.p[1].angle)
            angle_diff = np.clip(angle_diff, -self.ang_accel, self.ang_accel)

            attack = 1 if left_clicked else 0

            self.player_action = [dx, dy, angle_diff, attack]
        

        p0_screen = self.to_screen(self.p[0].pos)
        p1_screen = self.to_screen(self.p[1].pos)

        # Draw players
        pygame.draw.circle(self.window, (50, 150, 255), p0_screen, self.p[0].radius * self.scale)
        pygame.draw.circle(self.window, (255, 80, 80), p1_screen, self.p[1].radius * self.scale)

        # attacks
        ax0 = np.cos(self.p[0].angle)
        ay0 = np.sin(self.p[0].angle)
        if self.p[0].attack:
            pygame.draw.circle(self.window, (255, 255, 0), (p0_screen[0] + int(ax0 * 25), p0_screen[1] + int(ay0 * 25)), 10)

        # Draw attack direction
        end_x0 = p0_screen[0] + int(ax0 * 25)
        end_y0 = p0_screen[1] + int(ay0 * 25)
        pygame.draw.line(self.window, (255, 255, 0), p0_screen, (end_x0, end_y0), 3)

        # attacks
        ax1 = np.cos(self.p[1].angle)
        ay1 = np.sin(self.p[1].angle)
        if self.p[1].attack:
            pygame.draw.circle(self.window, (0, 255, 0), (p1_screen[0] + int(ax1 * 25), p1_screen[1] + int(ay1 * 25)), 10)

        # Draw attack direction
        end_x1 = p1_screen[0] + int(ax1 * 25)
        end_y1 = p1_screen[1] + int(ay1 * 25)
        pygame.draw.line(self.window, (255, 255, 0), p1_screen, (end_x1, end_y1), 3)

        # Health bars
        pygame.draw.rect(self.window, (0, 0, 255), (20, 20, 20 * self.p[0].health, 10)) # blue
        pygame.draw.rect(self.window, (255, 0, 0), (20, 40, 20 * self.p[1].health, 10)) # red

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
        action0 = env.action_space.sample()
        action1 = env.action_space.sample()
        obs, reward, terminated, truncated, _ = env.step(0, action0, action1)
        if terminated or truncated:
            obs, _ = env.reset()
        env.render()

    env.close()
