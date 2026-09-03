# PULL-torch Frequency Is Ambiguous Evidence

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
curriculum's sight potential exists to close.

Discriminating method, when it matters: log action counts over a run, or load
the checkpoint and sample its action distribution. "PULL up, USE flat" is the
signature of reject-avoidance; "PULL up, USE up following" is learned intent.
