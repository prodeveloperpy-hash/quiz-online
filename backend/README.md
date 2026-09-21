# Backend setup

1. Install Python 3.11+ and MySQL 8.
2. Run `mysql -u root -p < mysql_schema.sql`.
3. Copy `.env.example` to `.env` and set `DATABASE_URL`.
4. Create a virtual environment: `python -m venv .venv`.
5. Activate it on Windows: `.venv\Scripts\activate`.
6. Install packages: `pip install -r requirements.txt`.
7. Start API: `uvicorn app.main:app --reload`.

API documentation: http://localhost:8000/docs

For a quick test without MySQL, leave out `.env`; SQLite will be created automatically.

