# Daggorath Agent — Learnings & Concepts

_Expanded explanations of the ideas `design.md` relies on. The design doc records what we use and why in a line; this page unpacks the intention and proper use behind those things. Grow it as more is learned._

## Framework concepts

### Vectorized environments and `VecEnv`

`design.md` wraps the environment in `DummyVecEnv([make_env])`. This is what that actually means.

Stable-Baselines3's algorithms are written against an interface named `VecEnv` (`stable_baselines3.common.vec_env`) — **not** against a bare `gym.Env`. The interface's contract is an object holding one or more environment instances whose `reset()`/`step()` return batched results: an array of N observations, N rewards, N termination flags, and N info dicts, rather than single values. Every SB3 algorithm (PPO, SAC, DQN, …) collects rollouts through that batched interface, so a bare environment never reaches the algorithm directly.

Two concrete implementations ship with SB3:

- **`DummyVecEnv`** — runs its environments one at a time, in a `for` loop, in the current process. "Dummy" is SB3's own word for the no-parallelism placeholder. It is the right choice for a single environment or for debugging.
- **`SubprocVecEnv`** — spawns a separate worker process per environment and runs them genuinely in parallel. Use it as `SubprocVecEnv([make_env] * N)` when N environments should collect experience simultaneously.

**Proper use:** even a single environment must be wrapped, because the algorithms accept only the interface. Choose `DummyVecEnv` when N = 1; there is no parallelism to gain, so the multiprocessing machinery of `SubprocVecEnv` would be pure overhead.

Two other things share the name and are easy to confuse with SB3's:

- **`gymnasium.vector`** — Gymnasium's own vectorization module (`SyncVectorEnv`, `AsyncVectorEnv`). Same idea, different implementation, and its objects are **not** interchangeable with SB3's `VecEnv`.
- **`envpool`** — a separate third-party high-performance vectorizer. Not used here.

### `Dict` observations, `MultiInputPolicy`, and feature extractors

A `Dict` observation space needs SB3's `MultiInputPolicy`, which in turn uses a feature extractor to turn the dict into one flat feature vector. The built-in extractor (`CombinedExtractor`) routes a channel to a convolutional network only when SB3's `is_image_space` check accepts it — which means a 3-D channel whose last dimension is **1 or 3**. Our `map` channel is `(2, 32, 32)`: two channels, so it fails the check and falls through to a flattening MLP. A custom `BaseFeaturesExtractor` just re-implements that routing decision — that is the entire reason `DaggorathFeaturesExtractor` exists.

### Factored actions and joint masking

`MultiDiscrete([26, 31])` is a **factored** action: two independent axes, one per choice (verb form, object specifier). Per-axis masking — what masking libraries offer — can disable an item on one axis, but cannot express a **cross-axis** constraint such as "the object axis is limited only while the verb form is INCANT." A joint mask is a custom policy, not a mask array. That is why it is deferred here rather than wired in.

### Activation functions

A linear layer computes `W·x + b`. Stacking linear layers with nothing between them collapses into a single linear transform — matrix-multiplication associativity does the collapsing, so depth adds nothing. An **activation** is a nonlinear function applied element-wise between layers (ReLU: `max(0, x)`, the common default). That one bend is what lets the stack fit curves instead of a single straight line.

### Pooling vs. convolution

Both slide a small window across a feature map; the difference is what the window does.

- **Convolution** computes a *learned* dot product — the window values multiply trained weights. It has parameters.
- **Pooling** computes a *fixed* summary — the maximum or the average — with no learned parameters. It downsamples and adds a little tolerance to *where* a feature sits, but it is lossy by design.

For a small 32×32 input, pooling is optional.

### Stride

How far the sliding window jumps between steps. Stride 1 overlaps heavily and keeps the output near the input's size; stride 2 jumps two cells and roughly halves the spatial size. A stride-2 convolution downsamples *while still learning*, which is why the extractor uses it instead of pooling — no shrink discards information through a fixed summary.

### Flatten

A reshape from `(C, H, W)` to a vector of length `C·H·W`. No math, no weights — it is the adapter between a convolutional layer's spatial output and a dense layer's flat input. The flatten itself is free; the cost comes afterward.

### "Dense" vs. "1D"

Two unrelated axes of description. **Dense** (fully connected) describes *connectivity*: every input connects to every output with its own learned weight. **1D** describes *data shape*: a flat vector rather than a `(C, H, W)` volume. A dense layer accepts a 1D vector and emits one; it is not "made of" 1D vectors. The connection after a flatten explodes parameter count — each input element gets its own weight to each output — which is exactly why the CNN shrinks the spatial volume first, with shared kernels, before any dense layer sees it.

### Torch dtypes

torch has **no `uint16` tensor type**. SB3 converts observations with `torch.as_tensor`, which raises on `uint16`. `uint8` is accepted; this is the whole reason for the `uint16 → int32` observation wrapper.

## Operating lessons

### Wheels

A `.whl` file is a pre-built package archive — a ZIP containing the package already compiled and laid out. Its filename encodes name, version, Python version, and platform (`torch-2.13.0-cp312-...x86_64.whl`). `pip install` downloads that archive (or reuses a cached copy) and unzips it into the venv. "Using cached" in pip's output only means the download already happened — not that the package is installed.

### `--force-reinstall` is a sledgehammer

It uninstalls and rewrites every requested package, including the multi-hundred-MB CUDA wheels. When only one package is half-written, a targeted reinstall is the right tool; force-reinstall makes a small fix take a very long time.

### Never overlap `pip install` processes

Two concurrent `pip install`s corrupt each other's unzip step — that is precisely how torch's `lib/` ended up half-written here. Run one at a time.

### CUDA works under WSL

`nvidia-smi` under WSL reported an RTX 3080, and the torch install selected the `+cu130` build — `torch.cuda.is_available()` is `True`. No special setup was needed; pip's Linux wheel picked up the GPU-capable variant automatically.

### Python buffers stdout when redirected

Writing to a redirected file is block-buffered, so a running script's output can look empty until the process exits. Capture logs with `python -u` to flush immediately. This bit us during verification: the log appeared 0 bytes while the script was mid-run.