# Dataset inspection report

Inspection was performed on the supplied `Crop_recommendation.csv` on 2026-10-13. The file is intentionally not copied into this repository or committed by this project.

## Results

| Check | Result |
|---|---|
| Shape | 2,200 rows × 8 columns |
| Columns | `N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label` |
| Missing values | 0 in every column |
| Exact duplicate rows | 0 |
| Duplicate seven-feature vectors | 0 |
| Near duplicates after rounding all seven values to 1 decimal place | 0 |
| Classes | 22, with exactly 100 rows each |
| SHA-256 | `54a5a6e5408668e668667efc50de2fc867c1b875e0431b4f54dd331b0a109a4e` |

## Observed numeric ranges

| Feature | Minimum | Maximum | Mean |
|---|---:|---:|---:|
| N | 0.000 | 140.000 | 50.552 |
| P | 5.000 | 145.000 | 53.363 |
| K | 5.000 | 205.000 | 48.149 |
| temperature | 8.826 | 43.675 | 25.616 |
| humidity | 14.258 | 99.982 | 71.482 |
| ph | 3.505 | 9.935 | 6.470 |
| rainfall | 20.211 | 298.560 | 103.464 |

The CSV itself supplies no unit definitions, collection protocol, location, year, crop-management context, or source documentation. Humidity looks compatible with a percentage and pH is plausibly on the standard scale, but those are not verified by the source. N, P, K units and the rainfall aggregation period must be verified before farm use. The API reports this uncertainty instead of inventing units.

## Correlation and distribution notes

Pearson correlations show a strong positive P–K relationship (0.736). The next largest absolute pairwise association is N–P (-0.231); all other pairwise absolute correlations are at or below 0.205. Feature distributions should be reviewed per crop class during model evaluation, because global correlation does not show class separability. The balanced labels reduce class-frequency bias in this data, but may not reflect actual planting prevalence.

## Validation behavior

The reusable validator rejects missing, non-numeric, non-finite, blank-label, unexpected-column, and insufficient-class data. Its training audit records numeric ranges, quartiles, standard deviations, a Pearson correlation matrix, exact duplicate feature vectors, and feature vectors that collide after reproducible one-decimal rounding. These observations are reported for review only: the pipeline does not impute, delete observations, clip outliers, or silently correct values. Legitimate extreme values are retained. Request bounds are broad input-sanity bounds rather than data-derived agronomic limits.

## Engineered features

The baseline keeps only the seven source inputs. The optional engineered configuration preserves those seven and adds NPK total; N/P, N/K, and P/K ratios; temperature × humidity / 100; pH category; and rainfall category. Zero denominators deterministically produce `0.0`, avoiding infinities. pH categories are acidic `< 6.5`, near-neutral `6.5–7.5`, and alkaline `> 7.5`; rainfall categories are low `< 100`, medium `100–200`, and high `> 200`. These configurable thresholds are transparent heuristic bins, not claimed source-validated agronomic thresholds.
