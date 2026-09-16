# helm_intact

Run from the repository root:

```powershell
python -m helm.experiment run fixtures/scenarios/helm_intact.json --output results/helm_intact
python -m helm.experiment replay results/helm_intact/result.json
```

Output directories must be new. The scenario is a scripted synthetic test, not a probabilistic agent experiment.
