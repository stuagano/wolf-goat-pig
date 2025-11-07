---
name: gemini-dataset-validator
description: Validate datasets for Gemini supervised fine-tuning requirements
---

# Gemini Dataset Validator Skill

Validates datasets against Gemini SFT requirements for text, image, document, audio, and video tuning.

## Purpose

Ensure datasets meet Vertex AI Gemini supervised fine-tuning specifications before submitting tuning jobs.

## Dataset Requirements

### General Requirements
- Format: JSONL (JSON Lines)
- Minimum examples: 100-500 recommended for best results
- Location: Must be in Google Cloud Storage (GCS)
- Structure: Each line is a valid JSON object

### Supported Modalities
- Text datasets
- Image datasets (for vision tuning)
- Document datasets
- Audio datasets
- Video datasets

## Validation Checks

1. **File Format Validation**
   - Verify JSONL format
   - Check each line is valid JSON
   - Validate required fields are present

2. **Content Validation**
   - Check dataset size (minimum 100 examples)
   - Verify GCS URI format: `gs://bucket-name/path/to/file.jsonl`
   - Validate data structure matches modality requirements
   - Check for empty or malformed entries

3. **Token Count Analysis**
   - Estimate total billable tokens
   - Warn if dataset is too small or too large
   - Check individual example token counts

4. **Quality Checks**
   - Look for duplicate examples
   - Identify inconsistent formatting
   - Flag potential quality issues
   - Check label/response consistency

## Output Format

Provide validation results as:
```
✓ Format: Valid JSONL
✓ Location: gs://bucket/dataset.jsonl
✓ Example Count: 450 examples
✓ Token Count: ~125,000 tokens
⚠ Warning: Found 3 duplicate entries
✗ Error: 2 malformed JSON objects at lines 145, 278

Recommendations:
- Remove duplicate entries
- Fix malformed JSON objects
- Consider adding 50-100 more examples for optimal results
```

## Usage

Invoke this skill when:
- Preparing a new tuning dataset
- Debugging tuning job failures
- Validating data before expensive tuning runs
- Ensuring dataset quality standards
