"""AI pipeline entry point — OpenRouter / DeepSeek only."""
import json
import logging

from . import config, pipeline_openrouter
from .models import ProcessedOutput, RawArticle

log = logging.getLogger(__name__)


def run(raw_articles: list[RawArticle]) -> ProcessedOutput:
    return pipeline_openrouter.process(raw_articles)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not config.TMP_RAW.exists():
        print("✗ No raw articles found. Run `python -m veen.crawl` first.")
        return

    raw_data = json.loads(config.TMP_RAW.read_text())
    raw_articles = [RawArticle(**a) for a in raw_data]
    log.info("Loaded %d raw articles from %s", len(raw_articles), config.TMP_RAW)

    output = run(raw_articles)
    config.TMP_PROCESSED.write_text(output.model_dump_json(indent=2))
    print(
        f"✓ Processed {len(output.articles)} articles, "
        f"{len(output.clusters)} clusters → {config.TMP_PROCESSED}"
    )


if __name__ == "__main__":
    main()
