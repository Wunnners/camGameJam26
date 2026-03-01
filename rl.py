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
        self.atk_timer = 0
        self.radius = 0.6
        self.shield = False
        self.shield_timer = 0
        self.shield_start_timer = 0


class WorldEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    player_speed = 1

    def __init__(self, n_agents=1, render_mode="human"):
        super().__init__()
        self.render_mode = render_mode
        self.window = None

        # ===== Environment Parameters =====
        self.n_players = n_agents + 1
        self.arena_size = 10.0
        # self.scale = self.window_size // (self.arena_size * 2)
        self.scale = 50
        self.window_size = self.scale * self.arena_size
        self.max_health = 15
        self.attack_range = 1.8
        self.attack_angle = np.pi / 3
        self.atk_cd = 0.5
        self.shield_angle = np.pi / 4
        self.shield_slowdown = 0.5
        self.shield_cd = 0.5
        self.shield_broken_cd = 2.0
        self.shield_atk_cd = 0.1
        self.shield_start_cd = 0.5
        self.dt = 1 / 60

        self.accel = 0.6
        self.max_ang_accel = np.pi / 36

        # ===== Action Space =====
        # move_x, move_y, aim_accel, attack
        
        
        # self.action_space = spaces.Dict({
        #     "move": spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32),
        #     "rotate": spaces.Box(low=-1, high=1, shape=(1,), dtype=np.float32),
        #     "combat": spaces.Discrete(3) # 0=nothing,1=attack,2=shield
        # })
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        )

        # ===== Observation Space =====
        # dx, dy, self_cd, enemy_cd, self_hp, enemy_hp
        high = np.array(
            [
                self.arena_size, # p0 posx
                self.arena_size, # p0 posy
                1.0, # p0 velx
                1.0, # p0 vely
                1.0, # p0 cos delta ang
                1.0, # p0 sin delta ang
                1.0, # p0 ang vel
                1.0, # p1 cos ang
                1.0, # p1 sin ang
                1.0, # p1 ang vel
                self.atk_cd, # p0 atk cd
                self.atk_cd, # p1 atk cd
                self.max_health, # p0 health
                self.max_health, # p1 health
                self.shield_broken_cd, # p0 shield cd
                self.shield_broken_cd, # p1 shield cd
                self.shield_start_cd, # p1 shield start cd
                self.shield_start_cd, # p1 shield start cd
                1.0, # p0 shield
                1.0, # p1 shield
            ],
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
        self.p: list[Player] = [Player() for _ in range(self.n_players)]
        self.t = 0
        return (self._get_obs(0), {}), (self._get_obs(1), {})

    def set_pos(self, poss):
        for i, pos in enumerate(poss):
            self.p[i].pos = pos

    def _get_obs(self, idx=0):
        opidx = 0 if idx >= 1 else idx^1
        dx = self.p[opidx].pos[0] - self.p[idx].pos[0]
        dy = self.p[opidx].pos[1] - self.p[idx].pos[1]

        return np.array([
            dx,
            dy,
            self.p[idx].vel[0],
            self.p[idx].vel[1],
            np.cos(self._angle_diff(self.angle_to_enemy(idx), self.p[idx].angle)),
            np.sin(self._angle_diff(self.angle_to_enemy(idx), self.p[idx].angle)),
            self.p[idx].angle_vel,
            np.cos(self.p[opidx].angle),
            np.sin(self.p[opidx].angle),
            self.p[opidx].angle_vel,
            self.p[idx].atk_timer,
            self.p[opidx].atk_timer,
            self.p[idx].health,
            self.p[opidx].health,
            self.p[idx].shield_timer,
            self.p[opidx].shield_timer,
            self.p[idx].shield_start_timer,
            self.p[opidx].shield_start_timer,
            float(self.p[idx].shield),
            float(self.p[opidx].shield)
        ], dtype=np.float32)
    
    def angle_to_enemy(self, idx):
        opidx = 0 if idx >= 1 else idx^1
        dx = self.p[opidx].pos[0] - self.p[idx].pos[0]
        dy = self.p[opidx].pos[1] - self.p[idx].pos[1]
        return np.arctan2(dy, dx)

    def update_player(self, idx, action):
        if (self.p[idx].health <= 0): return

        opidx = 0 if idx >= 1 else idx ^ 1
        ridx = 0 if idx == 0 else 1

        # move_x, move_y = action["move"]
        # ang_accel = action["rotate"][0]
        # attack = action["combat"] == 1
        # shield = action["combat"] == 2
        move_x, move_y, ang_accel, combat = action
        attack = combat < -1/3
        shield = combat > 1/3
        # normalise
        ang_accel *= self.max_ang_accel

        self.p[idx].angle_vel += ang_accel
        self.p[idx].angle_vel *= 0.81
        self.p[idx].angle += self.p[idx].angle_vel
        self.p[idx].attack = False

        reward = [0.0, 0.0]
        terminated = False
        truncated = False

        # shield
        if shield and self.p[idx].shield_timer == 0:
            if not self.p[idx].shield:
                self.p[idx].shield_start_timer = self.shield_start_cd
            self.p[idx].shield = True
        elif self.p[idx].shield_start_timer == 0:
            if self.p[idx].shield:
                self.p[idx].atk_timer = self.shield_atk_cd
                self.p[idx].shield_timer = self.shield_atk_cd
            self.p[idx].shield = False

        # ===== Movement =====
        move_vec = np.array([move_x, move_y])
        norm = np.linalg.norm(move_vec)
        if norm > 1:
            move_vec = move_vec / norm

        shield_slowdown = self.shield_slowdown if self.p[idx].shield else 1.0
        self.p[idx].vel += move_vec * self.accel * shield_slowdown * self.dt
        self.p[idx].vel *= 0.91

        self.p[idx].pos += self.p[idx].vel
        # Clamp to arena
        self.p[idx].pos[0] = np.clip(self.p[idx].pos[0], -self.arena_size, -1)
        self.p[idx].pos[1] = np.clip(self.p[idx].pos[1], -self.arena_size, -1)

        # ===== Player Attack =====
        
        # self.p[idx].angle_vel += -np.clip(angle_diff, -self.max_ang_accel, self.max_ang_accel)*0.5 + np.random.uniform(-0.15, 0.15)
        # self.p[idx].angle_vel *= 0.81
        # self.p[idx].angle += self.p[idx].angle_vel

        hit = False
        ops = [opidx] if idx != 0 else range(1, self.n_players)
        for op in ops:
            dx = self.p[op].pos[0] - self.p[idx].pos[0]
            dy = self.p[op].pos[1] - self.p[idx].pos[1]
            distance = np.sqrt(dx**2 + dy**2)
            angle_to_enemy = np.arctan2(dy, dx)
            angle_from_enemy = np.arctan2(-dy, -dx)

            angle_diff = self._angle_diff(self.p[idx].angle, angle_to_enemy)

            if attack and self.p[idx].atk_timer == 0 and self.p[idx].shield_start_timer == 0:
                miss = True
                self.p[idx].attack = True
                if distance < self.attack_range:
                    enemy_angle_diff = np.abs(self._angle_diff(self.p[op].angle, angle_from_enemy))
                    if abs(angle_diff) < self.attack_angle:
                        kb = 0.2 if self.p[op].shield else 0.4
                        if not (self.p[op].shield and abs(enemy_angle_diff) < self.shield_angle):
                            self.p[op].health -= 1
                            reward[ridx] += 0.1
                            if idx != 0:
                                reward[op] -= 0.1
                        else:
                            reward[ridx] += 0.05
                            self.p[op].shield_timer = self.shield_broken_cd
                            self.p[op].atk_timer = self.shield_atk_cd
                            self.p[op].shield_start_timer = 0
                            self.p[op].shield = False
                        miss = False
                        self.p[op].vel += np.array([dx, dy]) / distance * kb
                        hit = True
                        break
                if miss:
                    reward[ridx] -= 0.03
        if attack and self.p[idx].atk_timer == 0 and self.p[idx].shield_start_timer == 0:
            self.p[idx].atk_timer = self.atk_cd
            self.p[idx].shield_timer = self.shield_cd
        
        # if distance < self.attack_range and attack:
        #     if self.p[opidx].shield:
        #         reward[ridx] += 0.005
        #     else:
        #         reward[ridx] += 0.05
        # elif attack and self.p[idx].atk_timer != 0:
        #     reward[ridx] -= 0.01
        
        # if shield and self.p[idx].shield_timer != 0:
        #     reward[ridx] -= 0.01

        # ===== Distance & Rotation Penalty =====
        reward[ridx] -= 0.001 * distance
        reward[ridx] -= 0.01 * abs(angle_diff)

        # ===== Cooldowns =====
        self.p[idx].atk_timer = max(0.0, self.p[idx].atk_timer - self.dt)
        self.p[idx].shield_timer = max(0.0, self.p[idx].shield_timer - self.dt)
        self.p[idx].shield_start_timer = max(0.0, self.p[idx].shield_start_timer - self.dt)

        # ===== Win/Loss =====
        if self.p[opidx].health <= 0:
            reward[ridx] += 1.0
            reward[opidx] -= 1.0
            terminated = True

        return self._get_obs(idx), reward, terminated, truncated, {}

    def step(self, idx, action0, actions):
        res = [None for _ in range(self.n_players)]
        # obs1, reward1, terminated1, truncated, info  = self.update_player(1, actions[0])
        res[0] = self.update_player(0, action0)
        for i in range(1, self.n_players):
            res[i - 1] = self.update_player(i, actions[i - 1])
        reward = res[0][0] + res[idx][1][0]

        for i in range(self.n_players):
            for j in range(i + 1, self.n_players):
                if (self.p[i].health <= 0 or self.p[j].health <= 0): continue
                self.resolve_collision(self.p[i], self.p[j])
        self.t += 1
        truncated = False
        if self.t > 500:
            truncated = True
        terminated = res[0][2] or res[idx][2]
        return res[idx][0], reward, terminated, truncated, res[0][4]

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
            center_x, center_y = self.to_screen(self.p[0].pos)
            angle = np.arctan2(mouse_y - center_y, mouse_x - center_x)
            angle_diff = self._angle_diff(angle, self.p[0].angle)
            angle_diff = np.clip(angle_diff, -1.0, 1.0)


            right_pressed = pygame.mouse.get_pressed()[2]
            shield = right_pressed
            attack = 1 if left_clicked else 0
            combat = 0
            if shield:
                combat = 1
            elif attack:
                combat = -1

            self.player_action = [dx, dy, angle_diff, combat]

        self.draw(0, (50, 150, 255)) # blue
        for i in range(1, self.n_players):
            self.draw(i, (255, 80, 80)) # red

        pygame.display.flip()
        self.clock.tick(60)

    def draw(self, idx, player_color):
        spos = self.to_screen(self.p[idx].pos)

        # draw player
        pygame.draw.circle(self.window, player_color, spos, self.p[idx].radius * self.scale)

        # draw attack
        angle = self.p[idx].angle
        ax = np.cos(angle)
        ay = np.sin(angle)
        if self.p[idx].attack:
            pygame.draw.circle(self.window, (255, 255, 0), (spos[0] + int(ax * 25), spos[1] + int(ay * 25)), 10)

        # Draw attack direction
        end_x = spos[0] + int(ax * 25)
        end_y = spos[1] + int(ay * 25)
        pygame.draw.line(self.window, (255, 255, 0), spos, (end_x, end_y), 3)

        # draw shieldd
        if self.p[idx].shield:
            offset = (self.p[idx].radius + 0.3) * self.scale
            shield_rect = pygame.rect.Rect(spos[0] - offset, spos[1] - offset, 2 * offset, 2 * offset)
            pygame.draw.arc(self.window, player_color, shield_rect, -(angle + self.shield_angle), -(angle - self.shield_angle), 5)

        # Health bar
        hpbar_top = 20 if idx == 0 else 40
        pygame.draw.rect(self.window, player_color, (20, hpbar_top, 20 * self.p[idx].health, 10))

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
