import os

import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from email.policy import default
from email.message import EmailMessage

# Import the functions from the module
from support import (
    parse_eml_standard,
    extract_email_attributes_standard,
    generate_email_hash,
    process_email_attributes,
    classify_email_with_groq,
    processed_hashes,
)

class TestEmailFunctions(unittest.TestCase):

    def setUp(self):
        self.sample_eml_content = b"From: test@example.com\nTo: recipient@example.com\nCc: cc@example.com\n\nThis is a test email."
        self.sample_eml_parsed = ('test@example.com', 'recipient@example.com', 'cc@example.com', 'This is a test email.')
        self.eml_folder = './test_emails'
        self.sample_body = "This is a test email."

    def test_parse_eml_standard(self):
        from_, to, cc, body = parse_eml_standard(self.sample_eml_content)
        self.assertEqual((from_, to, cc, body), self.sample_eml_parsed)

    @patch('os.listdir', return_value=['email1.eml', 'email2.eml'])
    @patch('builtins.open', new_callable=mock_open, read_data=b"From: test@example.com\nTo: recipient@example.com\nCc: cc@example.com\n\nThis is a test email.")
    def test_extract_email_attributes_standard(self, mock_open, mock_listdir):
        with patch('support.parse_eml_standard', return_value=self.sample_eml_parsed):
            email_tuples = extract_email_attributes_standard(self.eml_folder)
            self.assertEqual(len(email_tuples), 2)
            self.assertEqual(email_tuples[0][0], 'test@example.com')

    def test_generate_email_hash(self):
        email_hash = generate_email_hash(*self.sample_eml_parsed)
        self.assertEqual(len(email_hash), 32)

    @patch('support.generate_email_hash', return_value='dummy_hash')
    def test_process_email_attributes(self, mock_generate_email_hash):
        with patch('support.processed_hashes', set()):
            with patch('support.classify_email_with_groq', return_value='Spam'):
                process_email_attributes(*self.sample_eml_parsed, 'email1.eml', 0, 1)
                self.assertIn('bb45b58dcc3d00ee07c78186061269c4', processed_hashes)

    @patch('support.Groq')
    def test_classify_email_with_groq(self, mock_groq):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='Spam'))]
        )
        mock_groq.return_value = mock_client

        result = classify_email_with_groq(self.sample_body)
        self.assertEqual(result, 'Spam')

if __name__ == '__main__':
    unittest.main()