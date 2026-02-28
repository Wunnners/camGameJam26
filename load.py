from rl import WorldEnv
from stable_baselines3 import PPO

# a = PPO("MlpPolicy", WorldEnv(), verbose=2)
# a.load("model1")

env = WorldEnv()
a = PPO.load("modelBEST", env=env)


env = WorldEnv(render_mode="human")
obs, _ = env.reset()

for _ in range(1000):
    # action = a.predict(obs, None, None, True)[0]
    action = a.predict(obs, None, None, False)[0]
    print(env.p1_vel)
    obs, reward, terminated, truncated, _ = env.step(action)
    if terminated or truncated:
        obs, _ = env.reset()
    env.render()

env.close()