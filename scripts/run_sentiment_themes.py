# scripts/run_sentiment_themes.py
"""
CLI entry point for Task 2 sentiment + thematic analysis.
"""

import argparse
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.analysis.pipeline import SentimentThemePipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sentiment + thematic analysis pipeline.")
    parser.add_argument(
        "--input",
        default=None,
        help="Optional path to raw reviews CSV (defaults to config).",
    )
    parser.add_argument(
        "--output",
        default="data/processed/reviews_with_sentiment.csv",
        help="Path to save detailed review scores.",
    )
    parser.add_argument(
        "--sentiment-summary",
        default="data/processed/sentiment_summary.csv",
        help="Path to save aggregated sentiment summary.",
    )
    parser.add_argument(
        "--theme-summary",
        default="data/processed/theme_summary.csv",
        help="Path to save theme summary.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for transformer inference.",
    )
    parser.add_argument(
        "--model",
        default="distilbert-base-uncased-finetuned-sst-2-english",
        help="HuggingFace model name for sentiment classification.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = SentimentThemePipeline(sentiment_model=args.model, batch_size=args.batch_size)
    pipeline.run(
        raw_input_path=args.input,
        scored_output_path=args.output,
        sentiment_summary_path=args.sentiment_summary,
        theme_summary_path=args.theme_summary,
    )


if __name__ == "__main__":
    main()

