# helm_degraded

Run from the repository root:

```powershell
python -m helm.experiment run fixtures/scenarios/helm_degraded.json --output results/helm_degraded
python -m helm.experiment replay results/helm_degraded/result.json
```

Output directories must be new. The scenario is a scripted synthetic test, not a probabilistic agent experiment.
