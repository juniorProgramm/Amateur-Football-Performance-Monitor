# Amateur Football Monitor — Extended (Chart.js, Email, Migrations)

## Prerequisites
- Python 3.9+
- pip

## Setup
1. Create and activate virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Environment variables (recommended to put in a `.env` file and load via python-dotenv or set in OS):
   ```
   SECRET_KEY=your-secret
   DATABASE_URL=sqlite:///app.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
   ```

## Database migrations (Flask-Migrate)
1. Export FLASK_APP:
   ```bash
   export FLASK_APP=app.py   # Windows Powershell: $env:FLASK_APP="app.py"
   ```

2. Initialize migrations (only once):
   ```bash
   flask db init
   ```

3. Create migration (after model changes):
   ```bash
   flask db migrate -m "Initial migration"
   ```

4. Apply migration:
   ```bash
   flask db upgrade
   ```

## Run
```bash
python app.py
```

Open http://127.0.0.1:5000

Admin credentials (auto-created): username=admin password=adminpass — change immediately.

