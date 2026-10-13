"""Bootstrap pytest: repo root al sys.path para `import app...`."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
