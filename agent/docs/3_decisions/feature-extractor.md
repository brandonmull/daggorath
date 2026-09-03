# Feature Extractor

_1 Sep 2026_

## Decision

The observation is a six-channel `Dict`; the extractor routes the one spatial channel (`map`) through a small stride-2 CNN and the five flat channels through an MLP, then concatenates the two branches into one feature vector (`features_dim=256`).

## Why

- **The map is spatial; the rest is flat.** A CNN reads local wall and feature structure from the map; an MLP reads the flat scalars and entity tables directly.
- **SB3's built-in extractor can't do this.** It routes a channel to a CNN only when the channel's shape reads as an image (1 or 3 channels); the two-plane map fails that check and would fall through to the MLP, so the custom extractor re-implements the routing.

## What Changed

- `daggorath_agent/feature_extractor.py` — `DaggorathFeaturesExtractor` (CNN over `map`, MLP over the rest, concatenated).
- The CNN's output width is measured from a synthetic forward pass rather than hand-computed, so the final projection is exact by construction.
- It lives agent-side: the environment stays trainer-agnostic, and anything that fits a specific training library belongs here.
