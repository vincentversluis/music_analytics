import pathlib

# Point to the root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent

# Useful subpaths
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "databases" / "requests_cache.db"
