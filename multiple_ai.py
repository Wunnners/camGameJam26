from rl import WorldEnv
from stable_baselines3 import PPO
import pygame
import numpy as np

# a = PPO("MlpPolicy", WorldEnv(), verbose=2)
# a.load("model1")

env = WorldEnv(render_mode="human", n_agents=3)
a = PPO.load("ai/modelSELF28/final", env=env)
# a = PPO("MlpPolicy", env=env)

obs, _ = env.reset()

while True:
    # action0 = [0,0,0,0]
    action0 = env.player_action
    actions = [a.predict(env._get_obs(i), deterministic=False)[0] for i in range(1, env.n_players)]
    # print(actions)
    # obs, reward, terminated, truncated, _ = env.step(0, actions[0], [action0])
    obs, reward, terminated, truncated, _ = env.step(0, action0, actions)
    if terminated:
        break
    env.render()

env.close()