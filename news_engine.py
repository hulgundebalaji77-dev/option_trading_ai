import feedparser
import requests
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
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_live_sentiment(self) -> dict:
        scores = []
        try:
            # Requests द्वारे सेफ हेडरसह न्यूज फेच करणे
            response = requests.get(self.rss_url, headers=self.headers, timeout=10)
            feed = feedparser.parse(response.content)

            if hasattr(feed, 'entries') and feed.entries:
                for entry in feed.entries[:8]:
                    title = getattr(entry, 'title', '')
                    if title:
                        s = self.sia.polarity_scores(title)['compound']
                        scores.append(s)
        except Exception as e:
            print(f"News Fetch Error: {e}")

        # सेंटिमेंट कॅल्क्युलेशन
        avg = sum(scores) / len(scores) if scores else 0.0
        sentiment = "NEUTRAL"
        if avg >= 0.10:
            sentiment = "BULLISH"
        elif avg <= -0.10:
            sentiment = "BEARISH"

        return {
            "sentiment": sentiment,
            "score": round(avg, 3),
            "news_count": len(scores)
        }
