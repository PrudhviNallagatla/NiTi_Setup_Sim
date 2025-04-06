# Test Python environment and packages
import numpy as np
import matplotlib.pyplot as plt
import ase
import ovito
import freud
import pandas as pd
import scipy

print("Python environment test:")
print(f"NumPy version: {np.__version__}")
print(f"ASE version: {ase.__version__}")

# OVITO uses a different method to get version
try:
    from ovito import version
    print(f"OVITO version: {version.ovito_version}")
except (ImportError, AttributeError):
    print("OVITO version: Unable to determine version")

print(f"Freud version: {freud.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"SciPy version: {scipy.__version__}")

# Try to detect GPU
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("PyTorch not installed")

print("\nEnvironment test completed successfully!")

#----------------------------------------------------------------

import cupy as cp

# Print CUDA version
print("CUDA version:", cp.cuda.runtime.runtimeGetVersion())

# Test array creation and operation
x = cp.array([1, 2, 3])
print("CuPy array:", x)
print("Array squared:", x**2)

# Test GPU memory usage
print("Memory usage:")
print(cp.cuda.runtime.memGetInfo())
