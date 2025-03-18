# tests/conftest.py

"""Test configuration for the IaC framework."""

import pytest
import sys
import os

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
