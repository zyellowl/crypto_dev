import unittest
import os
import configparser
import sys

# Add project root to path to allow direct imports from 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.exchange import ExchangeManager
from core.resource_fetcher import ResourceFetcher
from core.analysis import Analysis

class TestCoreComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a dummy config file for all tests."""
        cls.config_file = os.path.join(os.path.dirname(__file__), 'test_config.ini')
        config = configparser.ConfigParser()
        config['API'] = {
            'BINANCE_API_KEY': 'TEST_KEY',
            'BINANCE_API_SECRET': 'TEST_SECRET',
            'OKX_API_KEY': 'TEST_KEY',
            'OKX_API_SECRET': 'TEST_SECRET',
            'OKX_API_PASSWORD': 'TEST_PASSWORD',
            # Try to get a real key from env for a live test, otherwise use a placeholder
            'NEWS_API_KEY': os.getenv('NEWS_API_KEY', 'YOUR_NEWS_API_KEY')
        }
        with open(cls.config_file, 'w') as f:
            config.write(f)

    @classmethod
    def tearDownClass(cls):
        """Remove the dummy config file after all tests."""
        os.remove(cls.config_file)

    def test_01_exchange_manager_loads(self):
        """Test that ExchangeManager loads exchanges correctly from the config."""
        print("\n--- [Test 1/4] Testing ExchangeManager ---")
        manager = ExchangeManager(config_file=self.config_file)
        self.assertIn('binance', manager.exchanges)
        self.assertIn('okx', manager.exchanges)
        print("✅ ExchangeManager loaded successfully.")

    def test_02_news_fetcher_init(self):
        """Test that NewsFetcher initializes and can fetch news if an API key is provided."""
        print("\n--- [Test 2/4] Testing NewsFetcher ---")
        fetcher = ResourceFetcher(config_file=self.config_file)
        self.assertIsNotNone(fetcher.api_key)
        
        if fetcher.api_key and fetcher.api_key != 'YOUR_NEWS_API_KEY':
            print("Attempting to fetch live news with provided API key...")
            news = fetcher.fetch_news('bitcoin', page_size=1)
            self.assertIsNotNone(news, "API call should return a response.")
            self.assertIn('articles', news, "Response should contain 'articles'.")
            print("✅ NewsFetcher fetched live news successfully.")
        else:
            print("⚠️ Skipping live NewsFetcher test: NEWS_API_KEY not found in environment.")
            print("   To run this test, set the NEWS_API_KEY environment variable.")

    def test_03_analysis_sentiment(self):
        """Test the sentiment analysis logic with sample data."""
        print("\n--- [Test 3/4] Testing Sentiment Analysis ---")
        analyzer = Analysis()
        sample_articles = [
            {'title': 'Bitcoin price soars to new all-time high! Fantastic news!'},
            {'title': 'Crypto market crashes spectacularly amid growing concerns.'}
        ]
        sentiment_df = analyzer.analyze_sentiment_of_articles(sample_articles)
        self.assertEqual(len(sentiment_df), 2)
        # Check that polarity is positive for the first title and negative for the second
        self.assertGreater(sentiment_df.loc[0, 'polarity'], 0.5, "Expected highly positive sentiment.")
        self.assertLess(sentiment_df.loc[1, 'polarity'], -0.5, "Expected highly negative sentiment.")
        print("✅ Sentiment analysis processed sample articles correctly.")

    def test_04_analysis_trading_signal(self):
        """Test the trading signal generation based on sentiment."""
        print("\n--- [Test 4/4] Testing Trading Signal Generation ---")
        analyzer = Analysis()
        
        # Test BUY signal
        positive_articles = [{'title': 'awesome amazing great success innovation crypto wins big'}]
        positive_df = analyzer.analyze_sentiment_of_articles(positive_articles)
        signal_buy = analyzer.generate_trading_signal(positive_df, threshold=0.5)
        self.assertEqual(signal_buy, 'BUY')
        print(f"✅ Generated signal for positive sentiment: {signal_buy}")

        # Test SELL signal
        negative_articles = [{'title': 'terrible horrible crash disaster scam lost all money'}]
        negative_df = analyzer.analyze_sentiment_of_articles(negative_articles)
        signal_sell = analyzer.generate_trading_signal(negative_df, threshold=0.5)
        self.assertEqual(signal_sell, 'SELL')
        print(f"✅ Generated signal for negative sentiment: {signal_sell}")

        # Test HOLD signal
        neutral_articles = [{'title': 'The crypto market is a thing that exists.'}]
        neutral_df = analyzer.analyze_sentiment_of_articles(neutral_articles)
        signal_hold = analyzer.generate_trading_signal(neutral_df, threshold=0.1)
        self.assertEqual(signal_hold, 'HOLD')
        print(f"✅ Generated signal for neutral sentiment: {signal_hold}")

if __name__ == '__main__':
    print("=============================================")
    print("  Running Core Component Tests")
    print("=============================================")
    print("This script will test the core functionalities of the application.")
    print("Make sure you have run 'pip3 install -r requirements.txt' and that")
    print("the textblob corpora download is complete.\n")
    unittest.main(verbosity=0) 