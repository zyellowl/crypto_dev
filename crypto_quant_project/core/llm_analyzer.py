import os
import configparser
from openai import OpenAI
import json

class LLMAnalyzer:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        if 'LLM' not in self.config:
            raise ValueError("LLM section not found in the config file.")
            
        self.api_key = self.config['LLM'].get('DEEPSEEK_API_KEY')
        self.base_url = self.config['LLM'].get('DEEPSEEK_API_BASE')

        if not self.api_key or self.api_key == 'YOUR_DEEPSEEK_API_KEY':
            raise ValueError("DEEPSEEK_API_KEY is not configured in the config file.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze_text(self, text: str) -> dict:
        """
        Analyzes the sentiment of a given text using the DeepSeek LLM.

        :param text: The text to analyze (e.g., news headline, tweet).
        :return: A dictionary with the analysis or None if an error occurs.
        """
        prompt = f"""
        Analyze the sentiment of the following text regarding its potential impact on the cryptocurrency market.
        The text is: "{text}"

        Your task is to determine if the sentiment is positive, negative, or neutral from a crypto investor's perspective.
        
        Please respond in a structured JSON format with the following fields:
        1. "sentiment_score": A float between -1.0 (very negative) and 1.0 (very positive).
        2. "confidence": A float between 0.0 (not confident) and 1.0 (very confident) in your assessment.
        3. "reasoning": A brief, one-sentence explanation for your analysis.
        
        Example response for a positive text:
        {{
          "sentiment_score": 0.8,
          "confidence": 0.9,
          "reasoning": "The text announces a significant technological breakthrough which is likely to be viewed positively by the market."
        }}
        
        Example response for a negative text:
        {{
          "sentiment_score": -0.7,
          "confidence": 0.85,
          "reasoning": "The text reports a major security breach, which typically leads to a loss of investor confidence."
        }}

        Now, analyze the provided text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,  # Set to 0 for deterministic output
                response_format={"type": "json_object"}
            )
            analysis_json = response.choices[0].message.content
            return json.loads(analysis_json)
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None

if __name__ == '__main__':
    # This example demonstrates how to use the LLMAnalyzer.
    # To run this, you MUST have a valid `config.ini` with a real DEEPSEEK_API_KEY.
    # Create a project root `config.ini` or place it in the core directory for this test.
    
    # Let's create a dummy config for this example if it doesn't exist
    config_path = '../config.ini'
    if not os.path.exists(config_path):
        print("Creating a dummy config.ini for demonstration.")
        print("You MUST replace YOUR_DEEPSEEK_API_KEY with a real key for this to work.")
        with open(config_path, 'w') as f:
            f.write("""
[LLM]
DEEPSEEK_API_KEY = YOUR_DEEPSEEK_API_KEY
DEEPSEEK_API_BASE = https://api.deepseek.com/v1
""")

    print("Running LLMAnalyzer module example...")
    try:
        analyzer = LLMAnalyzer(config_file=config_path)
        
        # --- Test Case 1: Positive News ---
        positive_text = "Ethereum's new EIP-4844 upgrade is live, drastically reducing transaction fees for Layer 2 solutions."
        print(f"\nAnalyzing positive text: '{positive_text}'")
        analysis_result = analyzer.analyze_text(positive_text)
        
        if analysis_result:
            print("LLM Analysis Result (Positive):")
            print(json.dumps(analysis_result, indent=2))
            assert isinstance(analysis_result.get('sentiment_score'), float)
            assert analysis_result.get('sentiment_score', 0) > 0
        else:
            print("Failed to get analysis for the positive text.")

        # --- Test Case 2: Negative News ---
        negative_text = "Major crypto exchange 'SecureX' halts withdrawals after discovering a $50 million hack."
        print(f"\nAnalyzing negative text: '{negative_text}'")
        analysis_result_neg = analyzer.analyze_text(negative_text)

        if analysis_result_neg:
            print("LLM Analysis Result (Negative):")
            print(json.dumps(analysis_result_neg, indent=2))
            assert isinstance(analysis_result_neg.get('sentiment_score'), float)
            assert analysis_result_neg.get('sentiment_score', 0) < 0
        else:
            print("Failed to get analysis for the negative text.")
            
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}") 