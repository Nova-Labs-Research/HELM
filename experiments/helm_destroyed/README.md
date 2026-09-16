# helm_destroyed

Run from the repository root:

```powershell
python -m helm.experiment run fixtures/scenarios/helm_destroyed.json --output results/helm_destroyed
python -m helm.experiment replay results/helm_destroyed/result.json
```

Output directories must be new. The scenario is a scripted synthetic test, not a probabilistic agent experiment.
