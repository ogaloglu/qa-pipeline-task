import configparser
import unittest
from unittest.mock import patch, Mock

from elasticsearch import Elasticsearch

from src.utils import (
    calculate_element_mrr,
    get_config,
    get_context,
    get_es,
    update_context,
)


class TestGetConfig(unittest.TestCase):
    def test_get_config(self):
        config_name = "es_config.ini"
        section_name = "ELASTIC"
        expected_options = ["cloud_id", "user", "password"]

        config = get_config(config_name)

        # Assert that required options exist within the config file
        self.assertIsInstance(config, configparser.ConfigParser)
        for option in expected_options:
            self.assertTrue(config.has_option(section_name, option))


class TestGetContext(unittest.TestCase):
    def setUp(self):
        # Create a mock Elasticsearch instance
        self.es = Mock(spec=Elasticsearch)

    def test_get_context(self):
        # Mock the Elasticsearch search response
        results = {
            "hits": {
                "hits": [
                    {"_source": {"context": "example1"}},
                    {"_source": {"context": "example2"}},
                ]
            }
        }
        self.es.search.return_value = results

        # Call the function with sample arguments
        question = "example question"
        index_name = "my_index"
        size = 2
        result = get_context(question, index_name, size, self.es)

        # Assert the expected result
        self.assertEqual(result, ["example1", "example2"])

        # Assert that Elasticsearch search method was called with the correct
        # arguments
        self.es.search.assert_called_once_with(
            index=index_name,
            body={"query": {"match": {"context": question}}},
            size=size,
        )


class TestGetES(unittest.TestCase):
    def setUp(self):
        # Read config files for hyperpameters and ES related information
        es_config = get_config("es_config.ini")

        self.cloud_id = es_config["ELASTIC"]["cloud_id"]
        self.user = es_config["ELASTIC"]["user"]
        self.password = es_config["ELASTIC"]["password"]

    def test_get_es_with_correct_inputs(self):
        # Assert that ES client is established with correct inputs
        es = get_es(self.cloud_id, self.user, self.password)
        self.assertIsInstance(es, Elasticsearch)
        es.info()

    def test_get_es_with_incorrect_inputs(self):
        # Assert that ES client is not estabilshed with incorrect inputs
        with self.assertRaises(Exception):
            es = get_es(self.cloud_id, self.user + "dummy", self.password)
            es.info()


class TestCalculateElementMRR(unittest.TestCase):
    def setUp(self):
        self.example = {"context": "answer", "question": "dummy"}
        self.index_name = "my_index"
        self.size = 2
        self.es = Mock(spec=Elasticsearch)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_with_answer_beginning(
        self,
        mock_get_context
    ):
        # Assert MRR is equal to 1 when the correct context is retieved first
        mock_get_context.return_value = ["answer", "answer"]
        updated_example = calculate_element_mrr(
            self.example, self.index_name, self.size, self.es
        )
        self.assertEqual(updated_example["mrr"], 1)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_with_answer_not_beginning(
        self,
        mock_get_context
    ):
        # Assert MRR is less than 1 and greater than zero when the correct
        # context is not retieved first but still within the retrieved contexts
        mock_get_context.return_value = ["dummy", "answer"]

        updated_example = calculate_element_mrr(
                self.example, self.index_name, self.size, self.es
        )
        self.assertEqual(updated_example["mrr"], 0.5)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_without_answer(
        self,
        mock_get_context
    ):
        # Assert MRR is 0 when the correct context is not retrieved at all
        mock_get_context.return_value = ["dummy", "dummy"]
        updated_example = calculate_element_mrr(
                self.example, self.index_name, self.size, self.es
        )
        self.assertEqual(updated_example["mrr"], 0.0)


class TestUpdateContext(unittest.TestCase):
    def setUp(self):
        self.example = {
            "question": "question",
            "context": "",
        }
        self.index_name = "my_index"
        self.size = 2
        self.es = Mock(spec=Elasticsearch)

    @patch("src.utils.get_context")
    def test_update_context(self, mock_get_context):
        # Mock the get_context function
        expected_context = ["answer", "answer"]
        mock_get_context.return_value = expected_context

        # Set up the mock return value of get_context
        updated_example = update_context(
                self.example, self.index_name, self.size, self.es
        )

        # Assert the context has been updated correctly
        self.assertEqual(
            updated_example["context"], " ".join(expected_context)
        )

        # Assert that get_context was called with the correct arguments
        mock_get_context.assert_called_once_with(
            self.example["question"], self.index_name, self.size, self.es
        )


if __name__ == "__main__":
    unittest.main()
