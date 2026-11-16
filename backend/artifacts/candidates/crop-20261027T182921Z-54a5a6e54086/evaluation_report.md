# Model comparison and evaluation

The winner was selected by mean macro F1 on training-only stratified CV. Held-out test metrics are reported for assessment and were not used as the selection rule.

| Configuration | Model | CV macro F1 | Held-out macro F1 | Accuracy | Training seconds | Model bytes |
|---|---:|---:|---:|---:|---:|---:|
| baseline | random_forest | 0.9937 | 0.9955 | 0.9955 | 1.07 | 1373554 |
| baseline | extra_trees | 0.9926 | 0.9932 | 0.9932 | 0.87 | 6363634 |
| engineered | random_forest | 0.9914 | 0.9932 | 0.9932 | 1.12 | 1420706 |
| engineered | extra_trees | 0.9862 | 0.9887 | 0.9886 | 0.92 | 5280546 |

## Selected candidate

- Version: `crop-20261027T182921Z-54a5a6e54086`
- Model: `random_forest`
- Feature configuration: `baseline`
- Held-out macro F1: `0.9955`

Model scores exposed by the API are classifier scores, not independently calibrated real-world crop-success probabilities.
