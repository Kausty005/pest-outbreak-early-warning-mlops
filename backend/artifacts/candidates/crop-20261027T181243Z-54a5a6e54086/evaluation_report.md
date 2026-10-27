# Model comparison and evaluation

The winner was selected by mean macro F1 on training-only stratified CV. Held-out test metrics are reported for assessment and were not used as the selection rule.

| Configuration | Model | CV macro F1 | Held-out macro F1 | Accuracy | Training seconds | Model bytes |
|---|---:|---:|---:|---:|---:|---:|
| baseline | random_forest | 0.9943 | 0.9955 | 0.9955 | 9.59 | 7282514 |
| baseline | extra_trees | 0.9914 | 0.9955 | 0.9955 | 8.10 | 31573874 |
| engineered | random_forest | 0.9925 | 0.9909 | 0.9909 | 10.43 | 6589986 |
| engineered | extra_trees | 0.9868 | 0.9932 | 0.9932 | 8.29 | 26146162 |

## Selected candidate

- Version: `crop-20261027T181243Z-54a5a6e54086`
- Model: `random_forest`
- Feature configuration: `baseline`
- Held-out macro F1: `0.9955`

Model scores exposed by the API are classifier scores, not independently calibrated real-world crop-success probabilities.
