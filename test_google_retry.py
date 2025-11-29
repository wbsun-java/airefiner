import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

# Mock time.sleep to speed up tests
time.sleep = MagicMock()

from models import model_loader

class TestGoogleRetry(unittest.TestCase):
    @patch('models.model_loader.genai')
    def test_fetch_google_models_retry(self, mock_genai):
        # Setup mock to fail twice then succeed
        # We need to return an iterable for the success case
        mock_model = MagicMock()
        mock_model.name = "models/gemini-pro"
        mock_model.supported_generation_methods = ['generateContent']
        
        mock_genai.list_models.side_effect = [
            Exception("504 Deadline Exceeded"),
            Exception("504 Deadline Exceeded"),
            [mock_model]
        ]
        
        # Mock is_text_model to return True
        with patch('models.model_loader.is_text_model', return_value=True):
            # Call the function
            print("Calling fetch_google_models...")
            models = model_loader.fetch_google_models("fake_key")
            
            # Verify it retried
            print(f"Call count: {mock_genai.list_models.call_count}")
            self.assertEqual(mock_genai.list_models.call_count, 3)
            self.assertEqual(len(models), 1)
            self.assertEqual(models[0]['model_name'], 'gemini-pro')
            print("Successfully verified retry logic!")

if __name__ == '__main__':
    unittest.main()
