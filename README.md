# Stone of Wunnn

## Inspiration

Time travel is tiring. When you travel back in time, all your hard work is lost! But what if that's not the case?
In this game, you can set your actions in stone and your future self will help you out with tasks!

## Enemy Training

### Proximal Policy Optimisation (PPO)

We use PPO reinforcement learning with DQN to train our enemy agents to support continuous observation state
and action space.

For advanced enemies, we deploy a multi agent training regime where the enemies play against each other (RL self training) in order for them to learn. The enemies are also set in stone: they are also trained against your move sequence and actions.

## Sound & Music

Every single sound track and effects is manually made in LMMS, a free and open source application.

Besides sfx, we feature 3 different tracks: normal Stone of Wunn theme, intense Stone of Wunn theme (remix), and menu music.
