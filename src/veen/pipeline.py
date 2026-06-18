"""Full pipeline convenience wrapper: crawl → AI → export."""
import json
import logging

from . import config
from .crawl import crawl
from .ai_pipeline import run
from .export import export


def run_pipeline() -> None:
    articles = crawl()
    config.TMP_RAW.write_text(
        json.dumps([a.model_dump() for a in articles], indent=2, default=str)
    )
    output = run(articles)
    config.TMP_PROCESSED.write_text(output.model_dump_json(indent=2))
    export()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline()


if __name__ == "__main__":
    main()
