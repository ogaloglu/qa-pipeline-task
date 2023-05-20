import configparser
import unittest
from unittest.mock import patch, Mock

from elasticsearch import Elasticsearch

from src.utils import (
    calculate_element_mrr,
    get_config,
    get_context,
    get_elastic_search_client,
    update_context,
    verify_config
)


class TestVerifyConfig(unittest.TestCase):
    def setUp(self):
        # Set up test configurations
        self.config_es = configparser.ConfigParser()
        self.config_hparams = configparser.ConfigParser()

        # Add necessary options for each configuration
        self.config_es.add_section("ELASTIC")
        self.config_es.set("ELASTIC", "cloud_id", "dummy")
        self.config_es.set("ELASTIC", "user", "dummy")
        self.config_es.set("ELASTIC", "password", "dummy")

        self.config_hparams.add_section("HYPERPARAMS")
        self.config_hparams.set("HYPERPARAMS", "model_checkpoint", "dummy")
        self.config_hparams.set("HYPERPARAMS", "context_size", "dummy")
        self.config_hparams.set("HYPERPARAMS", "index_name", "dummy")
        self.config_hparams.set("HYPERPARAMS", "qa_threshold", "dummy")

    def test_verify_config_with_valid_config(self):
        # Verify that a valid configuration returns True
        self.assertTrue(verify_config(self.config_es, "es_config"))
        self.assertTrue(verify_config(self.config_hparams, "hparams_config"))

    def test_verify_config_with_invalid_config(self):
        # Verify that an invalid configuration returns False
        invalid_config_es = configparser.ConfigParser()
        invalid_config_es.add_section("ELASTIC")
        invalid_config_es.set("ELASTIC", "cloud_id", "dummy")

        invalid_config_hparams = configparser.ConfigParser()
        invalid_config_hparams.add_section("SECTION")
        invalid_config_hparams.set("SECTION", "dummy", "dummy")

        self.assertFalse(verify_config(invalid_config_es, "es_config"))
        self.assertFalse(verify_config(invalid_config_hparams, "hparams_config"))


class TestGetConfig(unittest.TestCase):
    def test_get_config_with_incorrect_config_name(
        self
    ):
        config_name = "dummy_name"
        # Assert that file is not found with incorrect config name
        with self.assertRaises(FileNotFoundError):
            get_config(config_name)

    @patch("src.utils.verify_config")
    def test_get_config_with_verified_config_file(
        self, mock_verify_config
    ):
        config_name = "hparams_config"
        mock_verify_config.return_value = True

        get_config(config_name)

    @patch("src.utils.verify_config")
    def test_get_config_with_unverified_config_file(
        self, mock_verify_config
    ):
        config_name = "hparams_config"
        mock_verify_config.return_value = False
        # Assert that KeyError is raised with unverified config file
        with self.assertRaises(KeyError):
            get_config(config_name)


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
        es_config = get_config("es_config")

        self.cloud_id = es_config["ELASTIC"]["cloud_id"]
        self.user = es_config["ELASTIC"]["user"]
        self.password = es_config["ELASTIC"]["password"]

    def test_get_elastic_search_client_with_correct_inputs(self):
        # Assert that ES client is established with correct inputs
        es = get_elastic_search_client(self.cloud_id, self.user, self.password)
        self.assertIsInstance(es, Elasticsearch)
        es.info()

    def test_get_elastic_search_client_with_incorrect_inputs(self):
        # Assert that ES client is not estabilshed with incorrect inputs
        with self.assertRaises(Exception):
            es = get_elastic_search_client(
                self.cloud_id, self.user + "dummy", self.password
            )
            es.info()


class TestCalculateElementMRR(unittest.TestCase):
    def setUp(self):
        self.example = {"context": "answer", "question": "dummy"}
        self.index_name = "my_index"
        self.size = 2
        self.es = Mock(spec=Elasticsearch)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_with_answer_beginning(
        self, mock_get_context
    ):
        # Assert MRR is equal to 1 when the correct context is retieved first
        mock_get_context.return_value = ["answer", "answer"]
        updated_example = calculate_element_mrr(
            self.example, self.index_name, self.size, self.es
        )
        self.assertEqual(updated_example["mrr"], 1)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_with_answer_not_beginning(
        self, mock_get_context
    ):
        # Assert MRR is less than 1 and greater than zero when the correct
        # context is not retieved first but still within the retrieved contexts
        mock_get_context.return_value = ["dummy", "answer"]

        updated_example = calculate_element_mrr(
            self.example, self.index_name, self.size, self.es
        )
        self.assertEqual(updated_example["mrr"], 0.5)

    @patch("src.utils.get_context")
    def test_calculate_element_mrr_without_answer(self, mock_get_context):
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
        self.assertEqual(updated_example["context"], " ".join(expected_context))

        # Assert that get_context was called with the correct arguments
        mock_get_context.assert_called_once_with(
            self.example["question"], self.index_name, self.size, self.es
        )


if __name__ == "__main__":
    unittest.main()
