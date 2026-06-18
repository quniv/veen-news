import os
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]

# Load .env from repo root if present (local dev only; CI uses env vars directly)
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

DATA_DIR = REPO_ROOT / "data"
SOURCES_FILE = DATA_DIR / "sources.yaml"

TMP_RAW = Path("/tmp/veen-raw.json")
TMP_PROCESSED = Path("/tmp/veen-processed.json")

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
VEEN_AI_MODEL: str = os.getenv("VEEN_AI_MODEL", "deepseek/deepseek-v4-flash")
SCORE_THRESHOLD: float = float(os.getenv("VEEN_SCORE_THRESHOLD", "0.7"))
BATCH_SIZE: int = int(os.getenv("VEEN_BATCH_SIZE", "25"))
TITLE_BATCH_SIZE: int = int(os.getenv("VEEN_TITLE_BATCH_SIZE", "50"))
