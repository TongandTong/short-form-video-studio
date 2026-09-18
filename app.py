"""
Streamlit Cloud Entrypoint.
Delegates execution to web_app.py to ensure compatibility whether Streamlit Cloud
is configured to run streamlit_app.py or web_app.py.
"""

import runpy
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

app_path = BASE_DIR / "web_app.py"
runpy.run_path(str(app_path), run_name="__main__")
