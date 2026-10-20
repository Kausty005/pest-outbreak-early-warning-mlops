# Integration contracts

The crop service returns a normalized crop label, three ranked candidates, model version, UTC prediction timestamp, submitted inputs, model-score caveat, and disclaimer. A prediction is a recommendation event; it does not confirm planting.

## Crop recommendation response

```json
{
  "prediction_id": "uuid",
  "predicted_crop": "rice",
  "top_recommendations": [{"crop": "rice", "model_score": 0.84}],
  "model_version": "crop-...",
  "prediction_timestamp": "2026-10-13T10:00:00+00:00",
  "input_summary": {"N": 90.0, "P": 42.0, "K": 43.0, "temperature": 20.88, "humidity": 82.0, "ph": 6.5, "rainfall": 202.9},
  "confidence_note": "Model score is an uncalibrated class score...",
  "disclaimer": "Model-based prediction..."
}
```

## Lifecycle handoff

The farmer or another confirmed workflow must add a planting date. Do not infer it from a recommendation.

```json
{
  "farm_id": "optional-existing-farm-id",
  "selected_crop": "rice",
  "planting_date": "2026-06-10",
  "location": "optional farmer-supplied location",
  "model_version": "crop-..."
}
```

Future irrigation, nutrient, and disease services should use `crop`, lifecycle stage, real-time weather, IoT measurements, and farmer observations. Their models are explicitly out of scope here.

## Persistence schema

`farms` contains optional owner reference and location; `crop_predictions` stores inputs, ranked scores, version, and timestamp; `planting_records` tracks confirmed plantings and lifecycle state; `model_metadata` records training timestamp, metrics, and deployment status. Persistence is opt-in (`PERSISTENCE_ENABLED=true`) and unavailable databases do not block inference.
