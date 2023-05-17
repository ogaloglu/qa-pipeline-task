"""Evaluation script for the QA pipeline."""
import argparse
import logging
import os
from collections import Counter

from datasets import load_dataset
from evaluate import evaluator

from src.utils import calculate_element_mrr, get_config, get_es, update_context

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Evaluating the QA pipeline.")
    parser.add_argument(
        "--pipeline",
        type=str,
        required=True,
        help="Selection of the pipeline part to be evalated. Retrieval corresonds to only "
        "retrieval, reader corresponds to only reader and e2e corresponds to end-to-end pipeline.",
        choices=["retrieval", "reader", "e2e"],
    )
    parser.add_argument(
        "--val_set_size",
        type=int,
        default=None,
        help="Size of the validation set. A subset of the validation set can be used for quick"
        "experimentation.",
    )
    parser.add_argument(
        "--context_size",
        type=int,
        default=None,
        required=True,
        help="Number of contexts (responses) to be retrieved given a question (request).",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        required=True,
        help="Path of the validation set to be used for the evaluation.",
    )
    parser.add_argument(
        "--index_name",
        type=str,
        default="squad_dedup_validation",
        help="Index name of the validation set in the Elasticsearch cluster.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="distilbert-base-uncased-distilled-squad",
        help="Name of the pretrained model to be used for the pipeline.",
    )
    args = parser.parse_args()

    # Sanity checks
    if not os.path.exists(args.dataset_path):
        raise ValueError("Given path does not exist.")

    return args


def main():
    args = parse_arguments()
    logging.info("Arguments are obtained.")

    dataset = load_dataset("json", data_files=args.dataset_path, split="train")
    dataset = dataset.shuffle(seed=42)
    logging.info("Data is loaded and shuffled.")

    if args.val_set_size is not None or args.val_set_size < len(dataset):
        dataset = dataset.select(range(args.val_set_size))
        logging.info("A subset of the original dataset is selected.")

    logging.info(len(dataset))
    logging.info(dataset[:3])

    es_config = get_config("es_config.ini")
    logging.info("config.ini is read.")

    es = get_es(
        cloud_id=es_config["ELASTIC"]["cloud_id"],
        user=es_config["ELASTIC"]["user"],
        password=es_config["ELASTIC"]["password"],
    )
    logging.info("Elastic search connection is created.")

    match args.pipeline:
        case "retrieval":
            dataset = dataset.map(
                calculate_element_mrr,
                fn_kwargs={
                    "index_name": args.index_name,
                    "size": args.context_size,
                    "es": es,
                },
            )
            cnt = Counter(dataset["mrr"])
            # logging.info(
            #     f"MRR: {cnt[1] / len(dataset):.2%}, Ratio of answers "
            #     f"that are not captured within selected responses: {cnt[0] / len(dataset):.2%}"
            # )
            logging.info(
                f"MRR: {cnt[1] / len(dataset)}, Ratio of answers "
                f"that are not captured within selected responses: {cnt[0] / len(dataset)}"
            )
            # logging.info(f"{cnt[0] / len(dataset):.2%}")

        case "e2e" | "reader":
            if args.pipeline == "e2e":
                dataset = dataset.map(
                    update_context,
                    fn_kwargs={
                        "index_name": args.index_name,
                        "size": args.context_size,
                        "es": es,
                    },
                )
                logging.info(dataset[:3])

            task_evaluator = evaluator("question-answering")
            eval_results = task_evaluator.compute(
                model_or_pipeline=args.model_name,
                data=dataset,
                metric="squad",
            )

            logging.info(eval_results)


if __name__ == "__main__":
    main()
