# pip Tooling

## Wheels

A `.whl` file is a pre-built package archive — a ZIP containing the package already compiled and laid out. Its filename encodes name, version, Python version, and platform (`torch-2.13.0-cp312-...x86_64.whl`). `pip install` downloads that archive (or reuses a cached copy) and unzips it into the venv. "Using cached" in pip's output only means the download already happened — not that the package is installed.

## `--force-reinstall` is a sledgehammer

It uninstalls and rewrites every requested package, including the multi-hundred-MB CUDA wheels. When only one package is half-written, a targeted reinstall is the right tool; force-reinstall makes a small fix take a very long time.

## Never overlap `pip install` processes

Two concurrent `pip install`s corrupt each other's unzip step — that is precisely how torch's `lib/` ended up half-written here. Run one at a time.
