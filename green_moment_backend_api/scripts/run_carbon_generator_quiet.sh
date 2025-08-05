#!/bin/bash
# Run carbon intensity generator with suppressed warnings

cd "$(dirname "$0")/.."
source venv/bin/activate

# Suppress TensorFlow warnings
export TF_CPP_MIN_LOG_LEVEL=2
export TF_ENABLE_ONEDNN_OPTS=0

# Run the generator
python scripts/carbon_intensity_generator.py --scheduled 2>&1 | grep -v "AttributeError: 'MessageFactory'" | grep -v "CUDA" | grep -v "cuFFT" | grep -v "cuDNN" | grep -v "cuBLAS"