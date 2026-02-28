from rl import WorldEnv
from stable_baselines3 import PPO

a = PPO("MlpPolicy", WorldEnv(), verbose=2)
a.learn(total_timesteps=500000)
a.save("modelBEST")