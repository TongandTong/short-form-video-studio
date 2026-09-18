"""
Streamlit Cloud Entrypoint.
Delegates execution to web_app.py to ensure compatibility whether Streamlit Cloud
is configured to run streamlit_app.py or web_app.py.
"""

from pathlib import Path

app_path = Path(__file__).parent / "web_app.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

exec(code, globals())
