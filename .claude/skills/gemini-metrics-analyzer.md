---
name: gemini-metrics-analyzer
description: Analyze Gemini tuning and validation metrics to assess model performance
---

# Gemini Metrics Analyzer Skill

Analyzes tuning and validation metrics from Gemini supervised fine-tuning jobs to assess model performance and identify issues.

## Purpose

Interpret training metrics to determine if the model is learning effectively and make recommendations for improvement.

## Key Metrics

### Training Metrics (Auto-collected for Gemini 2.0 Flash and newer)

1. **`/train_total_loss`**
   - Loss for the training dataset at each step
   - **Good**: Steadily decreasing over time
   - **Bad**: Plateaus early, increases, or erratic fluctuations
   - **Action**: If not decreasing, increase epochs or learning rate

2. **`/train_fraction_of_correct_next_step_preds`**
   - Token accuracy on training data
   - Measures percentage of correctly predicted tokens
   - **Good**: Increasing trend, reaching 70-90%+
   - **Bad**: Stuck at low values (<50%) or not improving
   - **Action**: If low, check data quality or increase adapter size

3. **`/train_num_predictions`**
   - Number of tokens predicted at each step
   - Use to understand training data characteristics
   - Should be relatively consistent unless variable-length outputs

### Validation Metrics (Require validation dataset)

1. **`/eval_total_loss`**
   - Loss on validation dataset
   - **Good**: Decreases similarly to training loss
   - **Bad**: Increases while training loss decreases (overfitting)
   - **Action**: If overfitting, reduce learning rate or adapter size

2. **`/eval_fraction_of_correct_next_step_preds`**
   - Token accuracy on validation data
   - **Good**: Tracks training accuracy closely
   - **Bad**: Much lower than training accuracy (overfitting)
   - **Action**: Add more training data or use regularization

3. **`/eval_num_predictions`**
   - Number of tokens predicted on validation set

## Analysis Patterns

### Healthy Training
```
Train Loss: 2.5 → 1.8 → 1.3 → 0.9 → 0.7 (steady decrease)
Train Accuracy: 45% → 58% → 67% → 74% → 79% (steady increase)
Eval Loss: 2.6 → 1.9 → 1.4 → 1.0 → 0.8 (tracking train)
Eval Accuracy: 44% → 56% → 65% → 72% → 77% (tracking train)
```
**Interpretation**: Model is learning well, validation performance tracks training

### Overfitting
```
Train Loss: 2.5 → 1.5 → 0.8 → 0.4 → 0.2 (rapid decrease)
Train Accuracy: 45% → 65% → 82% → 91% → 96% (very high)
Eval Loss: 2.6 → 1.6 → 1.3 → 1.4 → 1.6 (increasing after epoch 2)
Eval Accuracy: 44% → 63% → 72% → 70% → 68% (declining)
```
**Interpretation**: Model memorizing training data, not generalizing
**Solution**: Reduce epochs, use smaller adapter, or add more training data

### Underfitting
```
Train Loss: 2.5 → 2.3 → 2.1 → 2.0 → 1.9 (slow decrease, plateaus)
Train Accuracy: 45% → 48% → 51% → 52% → 53% (minimal improvement)
Eval Loss: 2.6 → 2.4 → 2.2 → 2.1 → 2.0 (similarly slow)
Eval Accuracy: 44% → 47% → 49% → 50% → 51% (minimal improvement)
```
**Interpretation**: Model not learning enough from data
**Solution**: Increase adapter size, more epochs, or higher learning rate

### Unstable Training
```
Train Loss: 2.5 → 1.8 → 2.9 → 1.2 → 3.5 (erratic)
Train Accuracy: 45% → 58% → 42% → 68% → 35% (fluctuating)
```
**Interpretation**: Learning rate too high or data quality issues
**Solution**: Reduce learning rate multiplier to 0.5-0.8, check data quality

## Viewing Metrics

### In Vertex AI Studio Console
1. Go to Vertex AI Studio > Tune and Distill
2. Click on tuning job name
3. View **Monitor** tab for real-time metrics visualization

### Via API
```python
# Metrics are tracked in Vertex AI Experiments
tuning_job = client.tunings.get(name=tuning_job_name)
experiment = tuning_job.experiment
# Access experiment metrics via Vertex AI SDK
```

## Recommendations Output

```
=== Tuning Metrics Analysis ===

Training Progress: ✓ Healthy
- Train loss decreased from 2.5 → 0.8
- Train accuracy improved from 45% → 78%
- Stable convergence pattern

Validation Performance: ⚠ Slight Overfitting
- Eval loss: 2.6 → 1.1 (good)
- Eval accuracy: 44% → 72% (acceptable)
- Eval metrics slightly diverging from train after epoch 4

Recommendations:
1. Current model (epoch 4) shows best validation performance
2. Consider using checkpoint from epoch 4 instead of final epoch
3. For next iteration: reduce epochs to 4 or use ADAPTER_SIZE_FOUR

Overall: Model is performing well. Use epoch 4 checkpoint for deployment.
```
