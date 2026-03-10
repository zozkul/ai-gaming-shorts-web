import sys
import os

# Add the parent directory to sys.path so we can import from scripts
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from scripts import 1_extract_viral_clips as extractor
