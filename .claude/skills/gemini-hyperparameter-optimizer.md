---
name: gemini-hyperparameter-optimizer
description: Optimize hyperparameters for Gemini supervised fine-tuning jobs
---

# Gemini Hyperparameter Optimizer Skill

Recommends optimal hyperparameters for Gemini supervised fine-tuning based on dataset characteristics and use case.

## Purpose

Help users select appropriate hyperparameters for their Gemini tuning jobs to achieve optimal results.

## Key Hyperparameters

### 1. Epoch Count
- **What it is**: Number of complete passes over the training dataset
- **Default**: Auto-adjusted based on dataset size (recommended to use default)
- **When to adjust**:
  - Increase if model underfits (validation loss still decreasing)
  - Decrease if model overfits (validation loss increases while training loss decreases)

### 2. Adapter Size
- **What it is**: Number of trainable parameters for the tuning job
- **Options**: ADAPTER_SIZE_ONE (smallest), ADAPTER_SIZE_FOUR, ADAPTER_SIZE_EIGHT, ADAPTER_SIZE_SIXTEEN (largest)
- **Trade-offs**:
  - Larger adapter = Can learn more complex tasks but needs more data and time
  - Smaller adapter = Faster training, works with less data, but limited capacity
- **Recommendations**:
  - Small datasets (<500 examples): ADAPTER_SIZE_ONE or ADAPTER_SIZE_FOUR
  - Medium datasets (500-2000 examples): ADAPTER_SIZE_FOUR or ADAPTER_SIZE_EIGHT
  - Large datasets (>2000 examples): ADAPTER_SIZE_EIGHT or ADAPTER_SIZE_SIXTEEN

### 3. Learning Rate Multiplier
- **What it is**: Multiplier applied to the recommended learning rate
- **Default**: 1.0 (recommended)
- **When to adjust**:
  - Increase (1.5-2.0): To converge faster with stable, high-quality data
  - Decrease (0.5-0.8): To avoid overfitting or when training is unstable

## Optimization Strategy

1. **First Run - Use Defaults**
   ```python
   # Don't specify hyperparameters - let Vertex AI optimize
   tuning_job = client.tunings.tune(
       base_model="gemini-2.5-flash",
       training_dataset=training_dataset,
   )
   ```

2. **Analyze Metrics**
   - Monitor `/train_total_loss` and `/train_fraction_of_correct_next_step_preds`
   - If using validation dataset, monitor `/eval_total_loss` and `/eval_fraction_of_correct_next_step_preds`

3. **Adjust Based on Results**
   - **Underfitting**: Increase epochs or adapter size
   - **Overfitting**: Decrease learning rate, use smaller adapter, or add more training data
   - **Slow convergence**: Increase learning rate multiplier
   - **Unstable training**: Decrease learning rate multiplier

## Recommendations by Use Case

### Style/Format Adaptation
- Small changes to output format or style
- **Recommended**: Use defaults, possibly ADAPTER_SIZE_ONE for efficiency

### Domain-Specific Knowledge
- Teaching new terminology or domain concepts
- **Recommended**: ADAPTER_SIZE_FOUR to ADAPTER_SIZE_EIGHT, default epochs

### Complex Reasoning Tasks
- Multi-step reasoning, complex problem-solving
- **Recommended**: ADAPTER_SIZE_EIGHT to ADAPTER_SIZE_SIXTEEN, may need more epochs

### Multimodal Tasks
- Image, document, audio, or video understanding
- **Recommended**: ADAPTER_SIZE_EIGHT or larger, ensure sufficient examples per modality

## Export Checkpoints

- **Default**: Exports checkpoints at each epoch
- **Option**: Set `exportLastCheckpointOnly: true` to save only the final checkpoint
- **Benefit**: Saves storage costs if intermediate checkpoints aren't needed

## Output Format

Provide recommendations as:
```
Hyperparameter Recommendations for Your Use Case:

Dataset Size: 750 examples
Task Complexity: Medium (domain-specific Q&A)

Recommended Configuration:
- Epoch Count: Use default (auto-optimized)
- Adapter Size: ADAPTER_SIZE_FOUR
- Learning Rate Multiplier: 1.0 (default)
- Export Last Checkpoint Only: false

Rationale:
- Dataset size is sufficient for medium adapter
- Q&A task doesn't require largest adapter
- Start with defaults for optimal quality

Alternative Configuration (faster training):
- Adapter Size: ADAPTER_SIZE_ONE
- Trade-off: May sacrifice some quality for faster training
```
