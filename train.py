from rl import WorldEnv
from stable_baselines3 import PPO
import gymnasium as gym

import random

# a = PPO("MlpPolicy", WorldEnv(), verbose=2)
# a.learn(total_timesteps=500000)
# a.save("modelBEST")

model_name = "modelSELF28"
save_freq = 1


class WrapperEnv(gym.Env):
    """
    Exposes only the active agent to PPO.
    Other agent is handled internally (frozen/random).
    """
    def __init__(self, env: WorldEnv, active_player=0):
        self.env = env
        self.active_player = active_player
        self.opponent = None
        
        self.observation_space = env.observation_space
        self.action_space = env.action_space

    def reset(self, **kwargs):
        obs1, obs2 = self.env.reset(**kwargs)
        return obs1 if self.active_player == 0 else obs2

    def step(self, action):
        opponent_obs = self.env._get_obs(self.active_player ^ 1)

        # Active agent acts with PPO
        if self.active_player == 0:
            action1 = action
            action2 = self.get_opponent_action(opponent_obs)
        else:
            action2 = action
            action1 = self.get_opponent_action(opponent_obs)
        
        obs, reward, terminated, truncated, info = self.env.step(self.active_player, action1, action2)
        self.active_player ^= self.active_player
        return obs[0], reward[0], terminated, truncated, info
    
    def set_opponent(self, policy):
        self.opponent = policy
    
    def get_opponent_action(self, obs):
        return self.opponent.predict(obs)[0]


env = WrapperEnv(WorldEnv())
opponent_pool = []  # past versions of agent1
pool_sz = 5
idx = 0

n_eps = 10
batch_sz = 50000

model = PPO("MlpPolicy", env, verbose=2)

def freeze():
    frozen_opponent = PPO("MlpPolicy", env, verbose=0)
    frozen_opponent.policy.load_state_dict(model.policy.state_dict())
    return frozen_opponent


opponent_pool.append(freeze())

for episode in range(n_eps):
    print(f"\nEpisode {episode + 1} started\n")
    # Pick an opponent from pool (or random policy)
    env.set_opponent(random.choice(opponent_pool) if opponent_pool else None)

    model.learn(total_timesteps=batch_sz)

    # Periodically add current policy to opponent pool
    if episode % 50 == 0:
        if idx >= len(opponent_pool):
            opponent_pool.append(freeze())
        else:
            opponent_pool[idx] = freeze()
        idx = (idx + 1) % pool_sz
    
    if episode % save_freq == 0:
        model.save(f"{model_name}/ep{episode + 1}")

model.save(f"{model_name}/final")