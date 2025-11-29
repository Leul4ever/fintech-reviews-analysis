"""
High-level orchestration for Task 2 sentiment + thematic analysis.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.analysis.sentiment import SentimentAnalyzer
from src.analysis.themes import ThemeExtractor
from src.preprocessor import ReviewPreprocessor


@dataclass
class PipelineOutputs:
    scored_reviews_path: str
    sentiment_summary_path: str
    theme_summary_path: str


class SentimentThemePipeline:
    """Runs preprocessing → sentiment scoring → theme extraction."""

    def __init__(
        self,
        sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        batch_size: int = 32,
    ) -> None:
        self.sentiment = SentimentAnalyzer(model_name=sentiment_model, batch_size=batch_size)
        self.theme_extractor = ThemeExtractor()

    def _aggregate_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        grouped = (
            df.groupby(["bank", "rating"])
            .agg(
                mean_sentiment=("sentiment_score", "mean"),
                positive_share=("sentiment_label", lambda x: (x == "POSITIVE").mean()),
                negative_share=("sentiment_label", lambda x: (x == "NEGATIVE").mean()),
                review_count=("sentiment_label", "size"),
            )
            .reset_index()
        )
        return grouped

    def run(
        self,
        raw_input_path: Optional[str] = None,
        scored_output_path: str = "data/processed/reviews_with_sentiment.csv",
        sentiment_summary_path: str = "data/processed/sentiment_summary.csv",
        theme_summary_path: str = "data/processed/theme_summary.csv",
    ) -> PipelineOutputs:
        preprocessor = ReviewPreprocessor()
        if raw_input_path:
            preprocessor.input_path = raw_input_path
        if not preprocessor.load_data():
            raise FileNotFoundError("Raw reviews file could not be loaded.")
        clean_df = preprocessor.preprocess_data()
        if clean_df is None:
            raise RuntimeError("Preprocessing failed.")

        scored_df = self.sentiment.score_dataframe(clean_df, text_column="review", id_column="review_id")
        coverage = len(scored_df) / len(clean_df)
        print(f"Sentiment coverage: {coverage:.2%}")
        if coverage < 0.9:
            print("⚠️ Sentiment coverage below KPI (90%). Check empty reviews or preprocessing filters.")

        annotated_df = self.theme_extractor.annotate_reviews_with_themes(scored_df)
        theme_summary = self.theme_extractor.summarize_themes(annotated_df)
        sentiment_summary = self._aggregate_sentiment(scored_df)

        os.makedirs(os.path.dirname(scored_output_path), exist_ok=True)
        annotated_df.to_csv(scored_output_path, index=False)
        sentiment_summary.to_csv(sentiment_summary_path, index=False)
        theme_summary.to_csv(theme_summary_path, index=False)

        print(f"💾 Saved detailed reviews to {scored_output_path}")
        print(f"💾 Saved sentiment summary to {sentiment_summary_path}")
        print(f"💾 Saved theme summary to {theme_summary_path}")

        return PipelineOutputs(
            scored_reviews_path=scored_output_path,
            sentiment_summary_path=sentiment_summary_path,
            theme_summary_path=theme_summary_path,
        )

