import ast
import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from wordcloud import STOPWORDS, WordCloud

DATA_PATH = "data/processed/reviews_with_sentiment.csv"

BANK_NAME_TO_CODE = {
    "Commercial Bank of Ethiopia": "CBE",
    "Bank of Abyssinia": "BOA",
    "Dashen Bank": "DASHEN",
}

BANK_DISPLAY_NAME = {
    "CBE": "Commercial Bank of Ethiopia",
    "BOA": "Bank of Abyssinia",
    "DASHEN": "Dashen Bank",
}


@st.cache_data(show_spinner=False)
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.loc[:, ~df.columns.duplicated()]
    rename_map = {
        "review": "review_text",
        "review_date": "review_date",
        "date": "review_date",
        "bank": "bank_name",
        "bank_name": "bank_name",
        "sentiment": "sentiment_label",
        "theme": "themes",
    }
    df = df.rename(columns=rename_map)
    if "bank_code" not in df.columns:
        df["bank_code"] = df["bank_name"].map(BANK_NAME_TO_CODE)
    df["bank_code"] = df["bank_code"].fillna(df["bank_name"].map(BANK_NAME_TO_CODE)).fillna(df.get("bank_code")).str.upper()
    df["bank_name"] = df["bank_name"].fillna(df["bank_code"].map(BANK_DISPLAY_NAME)).fillna("Unknown")
    df["sentiment_label"] = df["sentiment_label"].astype(str).str.upper()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df = df.dropna(subset=["review_text", "rating", "review_date", "bank_code"])

    def parse_themes(value):
        if pd.isna(value):
            return []
        if isinstance(value, list):
            return value
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed]
        except (ValueError, SyntaxError):
            pass
        return [str(value).strip()] if value else []

    df["themes_list"] = df["themes"].apply(parse_themes) if "themes" in df.columns else [[] for _ in range(len(df))]
    df["year_month"] = df["review_date"].dt.to_period("M").dt.to_timestamp()
    return df.reset_index(drop=True)


def apply_filters(df: pd.DataFrame, bank: str, date_range, sentiments, rating_range):
    filtered = df.copy()
    if bank and bank != "All":
        filtered = filtered[filtered["bank_code"] == bank]
    if date_range and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered = filtered[(filtered["review_date"] >= start_date) & (filtered["review_date"] <= end_date)]
    if sentiments:
        filtered = filtered[filtered["sentiment_label"].isin(sentiments)]
    if rating_range and len(rating_range) == 2:
        filtered = filtered[(filtered["rating"] >= rating_range[0]) & (filtered["rating"] <= rating_range[1])]
    return filtered


def compute_kpis(df: pd.DataFrame):
    total_reviews = len(df)
    avg_rating = df["rating"].mean() if total_reviews else 0
    positive_pct = (df["sentiment_label"].eq("POSITIVE").mean() * 100) if total_reviews else 0
    negative_pct = (df["sentiment_label"].eq("NEGATIVE").mean() * 100) if total_reviews else 0
    return avg_rating, positive_pct, negative_pct, total_reviews


def plot_rating_distribution(df: pd.DataFrame):
    chart = px.histogram(
        df,
        x="rating",
        nbins=5,
        color_discrete_sequence=["#0D6EFD"],
        title="Rating Distribution",
    )
    chart.update_layout(bargap=0.1, xaxis_title="Rating", yaxis_title="Count")
    return chart


def plot_sentiment_by_bank(df: pd.DataFrame):
    grouped = df.groupby(["bank_code", "sentiment_label"]).size().reset_index(name="count")
    chart = px.bar(
        grouped,
        x="bank_code",
        y="count",
        color="sentiment_label",
        barmode="stack",
        title="Sentiment Distribution by Bank",
        color_discrete_map={"POSITIVE": "#2CA02C", "NEUTRAL": "#6C757D", "NEGATIVE": "#D7263D"},
    )
    chart.update_layout(xaxis_title="Bank", yaxis_title="Count", legend_title="Sentiment")
    return chart


def plot_sentiment_trend(df: pd.DataFrame):
    trend = (
        df.groupby(["year_month", "sentiment_label"])
        .size()
        .reset_index(name="count")
        .sort_values("year_month")
    )
    chart = px.line(
        trend,
        x="year_month",
        y="count",
        color="sentiment_label",
        markers=True,
        title="Sentiment Trend Over Time",
        color_discrete_map={"POSITIVE": "#2CA02C", "NEUTRAL": "#6C757D", "NEGATIVE": "#D7263D"},
    )
    chart.update_layout(xaxis_title="Month", yaxis_title="Count", legend_title="Sentiment")
    return chart


def plot_top_themes(df: pd.DataFrame, top_n: int = 8):
    exploded = df[["bank_code", "themes_list"]].explode("themes_list")
    exploded = exploded.dropna(subset=["themes_list"])
    counts = exploded.groupby(["bank_code", "themes_list"]).size().reset_index(name="count")
    counts = counts.sort_values(["bank_code", "count"], ascending=[True, False])
    counts = counts.groupby("bank_code").head(top_n)
    chart = px.bar(
        counts,
        x="themes_list",
        y="count",
        color="bank_code",
        barmode="group",
        title="Top Themes by Bank",
        color_discrete_sequence=["#0D6EFD", "#6F42C1", "#198754"],
    )
    chart.update_layout(xaxis_title="Theme", yaxis_title="Mentions", legend_title="Bank", xaxis_tickangle=-35)
    return chart


def build_wordcloud(df: pd.DataFrame) -> Image.Image | None:
    negatives = df[df["sentiment_label"] == "NEGATIVE"]
    text = " ".join(negatives["review_text"].astype(str).tolist())
    if not text.strip():
        return None
    wc = WordCloud(
        width=900,
        height=500,
        background_color="white",
        colormap="Reds",
        stopwords=STOPWORDS,
        max_words=150,
    )
    image = wc.generate(text).to_image()
    return image


def generate_insights(filtered: pd.DataFrame, comparison: pd.DataFrame):
    insights = []
    if not comparison.empty:
        bank_rating = comparison.groupby("bank_code")["rating"].mean().reset_index()
        top_bank = bank_rating.loc[bank_rating["rating"].idxmax()]
        insights.append(
            f"{BANK_DISPLAY_NAME.get(top_bank.bank_code, top_bank.bank_code)} has the highest average rating at {top_bank.rating:.2f}."
        )

        sentiment_counts = (
            comparison.groupby(["bank_code", "sentiment_label"])
            .size()
            .reset_index(name="count")
        )
        if not sentiment_counts.empty:
            sentiment_counts["total"] = sentiment_counts.groupby("bank_code")["count"].transform("sum")
            sentiment_counts["share"] = sentiment_counts["count"] / sentiment_counts["total"]
        neg = sentiment_counts[sentiment_counts["sentiment_label"] == "NEGATIVE"]
        if not neg.empty:
            worst_bank = neg.loc[neg["share"].idxmax()]
            insights.append(f"Negative sentiment is heaviest for {BANK_DISPLAY_NAME.get(worst_bank.bank_code, worst_bank.bank_code)} at {worst_bank.share*100:.1f}% of its reviews.")
    negative_reviews = filtered[filtered["sentiment_label"] == "NEGATIVE"]
    exploded = negative_reviews[["bank_code", "themes_list"]].explode("themes_list").dropna()
    if not exploded.empty:
        theme_counts = exploded.groupby(["bank_code", "themes_list"]).size().reset_index(name="count")
        top_theme = theme_counts.sort_values("count", ascending=False).iloc[0]
        insights.append(f"'{top_theme.themes_list}' is the most cited pain point for {BANK_DISPLAY_NAME.get(top_theme.bank_code, top_theme.bank_code)}.")
    recent_trend = (
        filtered.set_index("review_date")
        .groupby("sentiment_label")
        .resample("M")
        .size()
        .rename("count")
        .reset_index()
    )
    neg_trend = recent_trend[recent_trend["sentiment_label"] == "NEGATIVE"]
    if len(neg_trend) >= 2:
        last_two = neg_trend.sort_values("review_date").tail(2)
        delta = last_two["count"].iloc[-1] - last_two["count"].iloc[0]
        direction = "increased" if delta > 0 else "decreased"
        insights.append(f"Negative review volume has {direction} by {abs(int(delta))} in the latest month vs prior.")
    if not insights:
        insights.append("Data volume is low after filters; widen filters to see more insights.")
    return insights[:5]


def set_style():
    st.set_page_config(
        page_title="Customer Experience Analytics | Ethiopian Mobile Banking",
        layout="wide",
        page_icon="📱",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        .metric-card {background: #0b132b0d; padding: 16px 18px; border-radius: 12px; border:1px solid #e8eef5;}
        .insight-card {background: #f6f9fc; padding: 12px 14px; border-radius: 10px; margin-bottom: 8px; border:1px solid #e8eef5;}
        .st-emotion-cache-1rsyhoq {padding-top: 0;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    set_style()
    st.title("Customer Experience Analytics for Ethiopian Mobile Banking Apps")
    st.caption("Interactive review intelligence for CBE, BOA, and Dashen | Google Play data")

    df = load_data()
    min_date, max_date = df["review_date"].min().date(), df["review_date"].max().date()

    with st.sidebar:
        st.header("Filters")
        bank_option = st.selectbox("Bank", options=["All", "CBE", "BOA", "DASHEN"], index=0)
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        sentiment_options = st.multiselect("Sentiment", options=["POSITIVE", "NEUTRAL", "NEGATIVE"], default=["POSITIVE", "NEUTRAL", "NEGATIVE"])
        rating_range = st.slider("Rating", min_value=1, max_value=5, value=(1, 5), step=1)

    filtered_df = apply_filters(df, bank_option, date_range, sentiment_options, rating_range)
    comparison_base = apply_filters(df, "All", date_range, sentiment_options, rating_range)

    if filtered_df.empty:
        st.warning("No data available for the selected filters. Adjust filters to view insights.")
        return

    avg_rating, positive_pct, negative_pct, total_reviews = compute_kpis(filtered_df)
    kpi_cols = st.columns(4)
    kpi_cols[0].markdown(f"<div class='metric-card'><strong>Average Rating</strong><h2>{avg_rating:.2f}</h2></div>", unsafe_allow_html=True)
    kpi_cols[1].markdown(f"<div class='metric-card'><strong>% Positive</strong><h2>{positive_pct:.1f}%</h2></div>", unsafe_allow_html=True)
    kpi_cols[2].markdown(f"<div class='metric-card'><strong>% Negative</strong><h2>{negative_pct:.1f}%</h2></div>", unsafe_allow_html=True)
    kpi_cols[3].markdown(f"<div class='metric-card'><strong>Total Reviews</strong><h2>{total_reviews:,}</h2></div>", unsafe_allow_html=True)

    st.subheader("Experience Overview")
    col1, col2 = st.columns(2)
    col1.plotly_chart(plot_rating_distribution(filtered_df), use_container_width=True)
    col2.plotly_chart(plot_sentiment_by_bank(filtered_df), use_container_width=True)

    col3, col4 = st.columns(2)
    col3.plotly_chart(plot_sentiment_trend(filtered_df), use_container_width=True)
    col4.plotly_chart(plot_top_themes(filtered_df), use_container_width=True)

    st.subheader("Word Cloud — Negative Reviews")
    wc_image = build_wordcloud(filtered_df)
    if wc_image:
        buf = io.BytesIO()
        wc_image.save(buf, format="PNG")
        st.image(buf.getvalue(), use_column_width=True)
    else:
        st.info("Not enough negative reviews to generate a word cloud for the current filters.")

    st.subheader("Bank Comparison")
    compare_cols = st.columns(3)
    for idx, bank_code in enumerate(["CBE", "BOA", "DASHEN"]):
        bank_df = comparison_base[comparison_base["bank_code"] == bank_code]
        avg_r, pos_pct, neg_pct, total = compute_kpis(bank_df)
        bank_name = BANK_DISPLAY_NAME.get(bank_code, bank_code)
        compare_cols[idx].markdown(
            f"<div class='metric-card'><strong>{bank_name}</strong>"
            f"<p>Avg Rating: {avg_r:.2f}</p>"
            f"<p>Positive: {pos_pct:.1f}% | Negative: {neg_pct:.1f}%</p>"
            f"<p>Reviews: {total:,}</p></div>",
            unsafe_allow_html=True,
        )

    st.subheader("Insights")
    for insight in generate_insights(filtered_df, comparison_base):
        st.markdown(f"<div class='insight-card'>• {insight}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

