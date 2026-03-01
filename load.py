from rl import WorldEnv
from stable_baselines3 import PPO

# a = PPO("MlpPolicy", WorldEnv(), verbose=2)
# a.load("model1")

env = WorldEnv()
a = PPO.load("modelSELF24/final", env=env)

obs, _ = env.reset()

for _ in range(10000):
    # action = a.predict(obs, None, None, True)[0]
    action0 = a.predict(env._get_obs(0), deterministic=False)[0]
    action1 = a.predict(env._get_obs(1), deterministic=False)[0]
    obs, reward, terminated, truncated, _ = env.step(0, action0, action1)
    if terminated or truncated:
        obs, _ = env.reset()
    env.render()

env.close()