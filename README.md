Setup:

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Run:

streamlit run app/streamlit_app.py

Quality:

ruff check .

black .