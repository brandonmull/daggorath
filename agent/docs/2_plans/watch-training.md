# Watch Training — Plan

_What remains: strictly enforcing headless mode._

## Remaining

`window=False` today only omits `-window`; the launch does not emit `-video none`, so "headless" is not strictly enforced under WSLg. Enforcing it properly (`-video none`) is the remaining work.

## Reference

- Implemented: `../3_decisions/watch-training.md`
