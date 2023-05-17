import unittest
from unittest.mock import patch, MagicMock

from src.evaluate_pipeline import main


class TestScript(unittest.TestCase):
    @patch("src.evaluate_pipeline.len")
    @patch("src.evaluate_pipeline.parse_arguments")
    @patch("src.evaluate_pipeline.load_dataset")
    def test_main(self, mock_load_dataset, mock_parse_arguments, mock_len):
        # Mock dependencies
        mock_parse_arguments.return_value = MagicMock(
            pipeline="retrieval",
            dataset_path="path/to/dataset",
            val_set_size=10,
            context_size=2,
        )

        mock_dataset = MagicMock()
        mock_dataset.shuffle.return_value = mock_dataset
        mock_load_dataset.return_value = mock_dataset

        # Run main function
        main()

        # Assertions
        mock_load_dataset.assert_called_once_with(
            "json", data_files="path/to/dataset", split="train"
        )
        mock_dataset.shuffle.assert_called_once_with(seed=42)

        mock_dataset.select.assert_called()


if __name__ == "__main__":
    unittest.main()
