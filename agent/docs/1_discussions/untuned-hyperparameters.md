# Untuned Training Hyperparameters

Nothing in the agent has been tuned yet, and that's a gap to keep in view.

`train.py` builds the PPO model without setting any of the algorithm's own
knobs — the learning rate, how many steps it collects between updates, the
batch size, the discount factor. It just calls `PPO(...)`, and Stable-Baselines3
fills those in with its library defaults. That is not a decision so much as the
lack of one: no one has run experiments and picked a value; the values are
simply whatever the library shipped with.

The neural network is in the same state. The feature extractor's layer widths —
the CNN going 32 → 64 → 64 channels, the MLP at 128 hidden units, and the final
feature vector at 256 — were picked by hand when the extractor was written and
never compared against an alternative. They are reasonable first guesses, not
measured choices.

So the current agent is untuned, not decided. When a serious training run is in
scope, this is the first place to look: a sweep over the learning rate and the
extractor sizes is cheap relative to the MAME-paced environment, and these
untuned numbers are the most likely reason a first run underperforms.
