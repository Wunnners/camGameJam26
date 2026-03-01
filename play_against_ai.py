from rl import WorldEnv
from stable_baselines3 import PPO

# a = PPO("MlpPolicy", WorldEnv(), verbose=2)
# a.load("model1")

env = WorldEnv(render_mode="human")
a = PPO.load("ai/modelSELF28/final", env=env)
# a = PPO("MlpPolicy", env=env)

obs, _ = env.reset()

while True:
    action0 = a.predict(env._get_obs(0), deterministic=False)[0]
    # action0 = [0,0,0,0]
    action1 = env.player_action
    obs, reward, terminated, truncated, _ = env.step(0, action0, [action1])
    if terminated:
        break
    env.render()

env.close()