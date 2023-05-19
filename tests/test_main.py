import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app, get_context, get_es


class MyScriptTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("A self-documenting API", response.text)

    @patch("src.main.get_context")
    @patch("src.main.question_answerer")
    def test_extract_high_score(
        self, mock_question_answerer, mock_get_context
    ):
        mock_get_context.return_value = ["example1", "example2"]
        mock_question_answerer.return_value = {
            "answer": "answer",
            "score": 0.8,
        }
        response = self.client.post("/extract", json={"text": "question"})
        self.assertEqual(response.status_code, 200)
        # Assert returning the obtained answer for scores over the threshold
        self.assertEqual(response.json()["text"], "answer")

    @patch("src.main.get_context")
    @patch("src.main.question_answerer")
    def test_extract_low_score(
        self, mock_question_answerer, mock_get_context
    ):
        mock_get_context.return_value = ["example1", "example2"]
        mock_question_answerer.return_value = {
            "answer": "answer",
            "score": 0.3,
        }
        response = self.client.post("/extract", json={"text": "question"})
        self.assertEqual(response.status_code, 200)
        # Assert returning the default answer for scores under the threshold
        self.assertEqual(response.json()["text"], "Answer is not found.")

    @patch("src.main.get_context")
    @patch("src.main.question_answerer")
    def test_extract_es_returns_null(
        self, mock_question_answerer, mock_get_context
    ):
        mock_get_context.return_value = []
        response = self.client.post("/extract", json={"text": "question"})
        # Assert pipeline is not called
        mock_question_answerer.assert_not_called()
        self.assertEqual(response.status_code, 200)
        # Assert returning the default answer for scores under the threshold
        self.assertEqual(response.json()["text"], "Answer is not found.")


if __name__ == "__main__":
    unittest.main()
