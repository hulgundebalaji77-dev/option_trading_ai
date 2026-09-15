import feedparser
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

class NewsEngine:
    def _init_(self):
        self.sia = SentimentIntensityAnalyzer()
        self.rss_url = "https://news.google.com/rss/search?q=Nifty+50+Stock+Market+India&hl=en-IN&gl=IN&ceid=IN:en"

    def get_live_sentiment(self) -> dict:
        feed = feedparser.parse(self.rss_url)
        scores = []
        for entry in feed.entries[:8]:
            s = self.sia.polarity_scores(entry.title)['compound']
            scores.append(s)
            
        avg = sum(scores) / len(scores) if scores else 0.0
        sentiment = "NEUTRAL"
        if avg >= 0.15:
            sentiment = "BULLISH"
        elif avg <= -0.15:
            sentiment = "BEARISH"
            
        return {"sentiment": sentiment, "score": round(avg, 3)}
