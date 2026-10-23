import sys
import os

# Set VERCEL environment indicator for serverless runtime
os.environ["VERCEL"] = "1"

# Add root directory to sys.path so 'from application.main import app' works reliably
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from application.main import app
