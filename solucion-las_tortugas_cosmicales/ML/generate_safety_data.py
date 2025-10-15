import os
import sys
import pandas as pd

# Ensure ML package path is importable when running from project root
ML_DIR = os.path.dirname(os.path.abspath(__file__))
if ML_DIR not in sys.path:
	sys.path.insert(0, ML_DIR)

import main

RAW_PATH = os.path.join(ML_DIR, 'NYC_complaint_data.csv')
OUT_PATH = os.path.join(ML_DIR, 'safety_data.csv')

print('Loading raw complaints...')
df = main.load_and_preprocess_data(RAW_PATH)
print('Creating safety index...')
safety = main.create_safety_index(df)
print(f'Saving to {OUT_PATH}')
safety.to_csv(OUT_PATH, index=False)
print('Done')
