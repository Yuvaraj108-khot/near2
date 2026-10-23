import sys
import os

# Set VERCEL environment indicator and write to /tmp in serverless environments
os.environ["VERCEL"] = "1"
if not os.environ.get("DB_PATH"):
    os.environ["DB_PATH"] = "/tmp/settlement.db"

# Add application directory to sys.path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "application"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from main import app
