"""Training harness for the Daggorath Gym environment.

This package holds the agent side of the project: the feature extractor, the
observation wrappers, and the training pipeline that consumes `daggorath_gym`
as a library. It is editable-installed as `daggorath-agent`, but it is a
reference implementation, not a general-purpose library — it is run with
`python -m daggorath_agent.train`, not imported as a dependency, so this
package exports nothing.
"""