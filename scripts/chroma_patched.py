#!/usr/bin/env python3
"""
Compatibility wrapper script for ChromaDB to work with NumPy 2.0
This script patches the incompatible type references before importing ChromaDB.
"""

import os
import sys
import importlib
import types

def monkey_patch_numpy():
    """
    Add back deprecated NumPy types as aliases to maintain compatibility with ChromaDB
    """
    import numpy as np
    
    # Add back deprecated types that were removed in NumPy 2.0
    if not hasattr(np, 'float_'):
        np.float_ = np.float64
    
    if not hasattr(np, 'int_'):
        np.int_ = np.int64
    
    if not hasattr(np, 'uint'):
        np.uint = np.uint64
    
    if not hasattr(np, 'bool_'):
        np.bool_ = np.bool
    
    # Return patched numpy module
    return np

def patch_chromadb():
    """
    Patch ChromaDB to work with NumPy 2.0
    """
    # First apply numpy patch
    monkey_patch_numpy()
    
    # Now we can safely import chromadb
    import chromadb
    return chromadb

# Apply patches before importing
patched_chromadb = patch_chromadb()

# Make the patched module available
sys.modules['chroma_patched'] = types.ModuleType('chroma_patched')
sys.modules['chroma_patched'].chromadb = patched_chromadb

# Export the patched chromadb module
chromadb = patched_chromadb

if __name__ == "__main__":
    print("ChromaDB patched successfully for NumPy 2.0 compatibility.")
    print(f"ChromaDB version: {chromadb.__version__}") 