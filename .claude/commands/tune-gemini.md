---
description: Launch Gemini supervised fine-tuning workflow with expert guidance
---

You are helping create and manage a Gemini supervised fine-tuning job on Vertex AI.

## Your Task

Guide the user through the complete Gemini tuning workflow:

1. **Understand Requirements**
   - Ask about the use case and desired model behavior
   - Clarify which modality (text, image, document, audio, video)
   - Determine if they have training data ready

2. **Dataset Preparation**
   - Validate dataset format (JSONL required)
   - Check dataset location (must be in GCS)
   - Verify dataset size (recommend 100-500+ examples)
   - Offer to create validation dataset if not provided

3. **Model & Hyperparameter Selection**
   - Recommend base model (gemini-2.5-flash is most common)
   - Suggest hyperparameters based on dataset size:
     - Start with defaults for first run
     - Explain adapter size options
     - Discuss epoch count and learning rate

4. **Launch Tuning Job**
   - Create tuning job using appropriate SDK (Vertex AI or Gen AI)
   - Configure training and validation datasets
   - Set hyperparameters (or use defaults)
   - Enable automatic evaluation if desired

5. **Monitor Progress**
   - Poll job status regularly
   - Report training metrics as they become available
   - Alert on any issues or anomalies
   - Estimate completion time

6. **Evaluate Results**
   - Retrieve tuned model endpoint
   - Test model with sample prompts
   - Compare against base model
   - Analyze metrics and checkpoints

7. **Provide Deployment Guidance**
   - Generate integration code
   - Document endpoint details
   - Provide cost estimates
   - Suggest monitoring strategies

## Key Information

**Supported Models**:
- gemini-2.5-flash (recommended for most use cases)
- gemini-2.5-pro (for complex tasks)
- gemini-2.5-flash-lite (for fast, efficient tuning)
- gemini-2.0-flash, gemini-2.0-flash-lite

**Dataset Requirements**:
- Format: JSONL (JSON Lines)
- Location: Google Cloud Storage
- Size: Minimum 100 examples, 100-500 recommended
- Validation dataset: Optional but recommended

**Hyperparameters**:
- Epochs: Auto-adjusted (recommended to use default)
- Adapter Size: ONE, FOUR, EIGHT, SIXTEEN
- Learning Rate Multiplier: Default 1.0

**Regions**: us-central1, europe-west4, asia-northeast1

## Best Practices

1. Start with defaults - don't tune hyperparameters on first run
2. Always use a validation dataset to detect overfitting
3. Monitor metrics in real-time via Vertex AI Studio
4. Test multiple checkpoints before deployment
5. For thinking models, disable thinking budget after tuning

## Resources

- Check existing code for Vertex AI integration patterns
- Reference app/services/vertex_* files for current implementation
- Look for GCS bucket configuration in .env or config files
- Review any existing tuning jobs or datasets

Begin by asking the user what they want to accomplish with Gemini fine-tuning.
