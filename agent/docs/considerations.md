# Design Considerations

Ideas and observations from working with the project, not yet decided. No code.

## PULL-torch frequency is ambiguous evidence

Watching a training run, the agent began issuing PULL (PINE) TORCH more
often. On its own that is compatible with two very different readings:

1. Learned torch-value — the agent is gravitating toward torch acquisition
   because lighting it eventually pays (visibility → new cells → advance).
2. Reject-avoidance — only the −0.1 "???" penalty and the advance bonus are
   sharp right now. If the torch is the sole pullable floor object in reach,
   then PULL TORCH is simply the only PULL that does not get rejected. The
   agent may be fleeing a penalty, not seeking a torch.

The decider is whether USE follows PULL. If it does not, the agent has
learned to pull but not to light — the credit-assignment gap that the
curriculum plan's sight potential exists to close.

Discriminating method, when it matters: log action counts over a run, or load
the checkpoint and sample its action distribution. "PULL up, USE flat" is the
signature of reject-avoidance; "PULL up, USE up following" is learned intent.

## The training hyperparameters are still first guesses

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