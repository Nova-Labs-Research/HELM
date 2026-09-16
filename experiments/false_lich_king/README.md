# false_lich_king

Run from the repository root:

```powershell
python -m helm.experiment run fixtures/scenarios/false_lich_king.json --output results/false_lich_king
python -m helm.experiment replay results/false_lich_king/result.json
```

Output directories must be new. The scenario is a scripted synthetic test, not a probabilistic agent experiment.
