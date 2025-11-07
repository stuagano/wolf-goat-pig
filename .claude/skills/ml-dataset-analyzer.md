---
name: ml-dataset-analyzer
description: Analyze ML datasets for quality, distribution, and potential issues
---

# ML Dataset Analyzer Skill

Analyzes machine learning datasets to assess quality and identify potential issues.

## Purpose

Evaluate datasets used for image generation and LLM training, focusing on:
- Data distribution and balance
- Label quality and consistency
- Image quality metrics
- Potential biases or gaps

## Instructions

When invoked, this skill will:

1. Identify dataset locations (GCS buckets, local files, or Vertex AI datasets)
2. Sample and analyze data distribution
3. Check for common issues:
   - Class imbalance
   - Missing or corrupted files
   - Label inconsistencies
   - Duplicate entries
4. Generate a report with:
   - Summary statistics
   - Visualization recommendations
   - Quality metrics
   - Actionable recommendations

## Output Format

Provide results as:
- Dataset statistics table
- Issues found (categorized by severity)
- Recommendations for improvement
