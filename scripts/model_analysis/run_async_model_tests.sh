#!/bin/bash

# Run async model tests
# This script runs the async_model_test.py script with the specified parameters

# Default values
OUTPUT_DIR="/app/model_test_results"
MAX_CONCURRENT=1
QUANTIZATION="none"  # Default to no quantization for compatibility
FLASH_ATTENTION="false"  # Default to no flash attention for compatibility
TEMPERATURE="0.7"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --models)
      MODELS="$2"
      shift 2
      ;;
    --max-concurrent)
      MAX_CONCURRENT="$2"
      shift 2
      ;;
    --quantization)
      QUANTIZATION="$2"
      shift 2
      ;;
    --flash-attention)
      FLASH_ATTENTION="$2"
      shift 2
      ;;
    --temperature)
      TEMPERATURE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set timestamp for output file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${OUTPUT_DIR}/async_model_test_${TIMESTAMP}.json"

# Run the async model test script
echo "Running async model tests..."
echo "Max concurrent tests: $MAX_CONCURRENT"
echo "Output file: $OUTPUT_FILE"

if [ -n "$MODELS" ]; then
  echo "Testing models: $MODELS"
  python3 /app/scripts/async_model_test.py \
    --models $MODELS \
    --quantizations $QUANTIZATION \
    --flash-attention $FLASH_ATTENTION \
    --temperatures $TEMPERATURE \
    --max-concurrent $MAX_CONCURRENT \
    --output "$OUTPUT_FILE"
else
  echo "Testing all available models"
  python3 /app/scripts/async_model_test.py \
    --quantizations $QUANTIZATION \
    --flash-attention $FLASH_ATTENTION \
    --temperatures $TEMPERATURE \
    --max-concurrent $MAX_CONCURRENT \
    --output "$OUTPUT_FILE"
fi

echo "Tests completed. Results saved to $OUTPUT_FILE"
