"""
Sentiment scoring utilities using HuggingFace transformers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd
from transformers import pipeline


def _normalize_label(label: str) -> str:
    label_up = label.upper()
    if "POS" in label_up:
        return "POSITIVE"
    if "NEG" in label_up:
        return "NEGATIVE"
    return label_up


@dataclass
class SentimentResult:
    text: str
    sentiment_label: str
    sentiment_score: float
    positive_score: float
    negative_score: float


class SentimentAnalyzer:
    """
    Thin wrapper around the `distilbert-base-uncased-finetuned-sst-2-english` model.

    Produces POSITIVE / NEGATIVE / NEUTRAL labels plus a signed sentiment score.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        batch_size: int = 32,
        neutral_threshold: float = 0.1,
        device: Optional[int] = None,
    ) -> None:
        self.batch_size = batch_size
        self.neutral_threshold = neutral_threshold
        self.model_name = model_name
        self.classifier = pipeline(
            "text-classification",
            model=model_name,
            return_all_scores=True,
            device=device if device is not None else -1,
        )

    def score_texts(self, texts: Iterable[str]) -> List[SentimentResult]:
        cleaned_texts = [text if isinstance(text, str) and text.strip() else "" for text in texts]
        outputs = []
        for start in range(0, len(cleaned_texts), self.batch_size):
            chunk = cleaned_texts[start : start + self.batch_size]
            outputs.extend(self.classifier(chunk))

        results: List[SentimentResult] = []
        for text, scores in zip(cleaned_texts, outputs):
            pos_score = next((s["score"] for s in scores if _normalize_label(s["label"]) == "POSITIVE"), 0.0)
            neg_score = next((s["score"] for s in scores if _normalize_label(s["label"]) == "NEGATIVE"), 0.0)
            signed = pos_score - neg_score
            if signed > self.neutral_threshold:
                label = "POSITIVE"
            elif signed < -self.neutral_threshold:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"

            results.append(
                SentimentResult(
                    text=text,
                    sentiment_label=label,
                    sentiment_score=signed,
                    positive_score=pos_score,
                    negative_score=neg_score,
                )
            )
        return results

    def score_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str = "review",
        id_column: Optional[str] = "review_id",
    ) -> pd.DataFrame:
        texts = df[text_column].fillna("").astype(str).tolist()
        results = self.score_texts(texts)
        scored_df = pd.DataFrame(
            [{
                "sentiment_label": r.sentiment_label,
                "sentiment_score": r.sentiment_score,
                "positive_score": r.positive_score,
                "negative_score": r.negative_score,
            } for r in results]
        )
        if id_column and id_column in df.columns:
            scored_df[id_column] = df[id_column].values
        return pd.concat([df.reset_index(drop=True), scored_df], axis=1)

