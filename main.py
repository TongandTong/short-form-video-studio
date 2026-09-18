"""
Main Entrypoint for Streamlit Cloud and Server Deployments.
Executes web_app.py seamlessly so that whether Streamlit Cloud is configured to
main.py, streamlit_app.py, or web_app.py, the application runs instantly.
"""

from pathlib import Path

app_path = Path(__file__).parent / "web_app.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

exec(code, globals())
