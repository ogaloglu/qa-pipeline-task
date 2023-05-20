"""Utility functions."""
import configparser
from pathlib import Path
from typing import Any, Dict, List

from elasticsearch import Elasticsearch

CONFIG_DICT = {
    "es_config": [
        ("ELASTIC", item) for item in ("cloud_id", "user", "password")
    ],
    "hparams_config": [
        ("HYPERPARAMS", item)
        for item in (
            "model_checkpoint",
            "context_size",
            "index_name",
            "qa_threshold",
        )
    ],
}


def verify_config(config: configparser.ConfigParser, config_name: str) -> bool:
    """Verify if a configuration file has all necessary section-key pairs.

    Args:
        config (configparser.ConfigParser): Config object to be verified.
        config_name (str): Name of the config within configs directory.

    Returns:
        bool: True if the config file has all necessary section-key pairs,
        False otherwise.
    """
    return all(
        [
            config.has_option(*section_key_pair)
            for section_key_pair in CONFIG_DICT[config_name]
        ]
    )


def get_config(config_name: str) -> configparser.ConfigParser:
    """Read the respective config.ini file and return a config object.

    Args:
        config_name (str): Name of the config within configs directory.

    Returns:
        configparser.ConfigParser: Config object.
    """
    config = configparser.ConfigParser()
    config_file_path = (
        Path(__file__).parent / ".." / f"configs/{config_name}.ini"
    )
    with open(config_file_path) as file:
        config.read_file(file)

    if not verify_config(config, config_name):
        raise KeyError(
            f"{config_name}.ini file does not have all necessary section-key "
            "pairs. The required section-keys are as follows: "
            f"{CONFIG_DICT[config_name]}"
        )
    return config


def get_context(
    question: str, index_name: str, size: int, es: Elasticsearch
) -> List[str]:
    """Retrieve the list of the most relevant contexts given a question from
    Elasticsearch cluster.

    Args:
        question (str): Question that used as the query.
        index_name (str): Name of the index for retrieving the data.
        size (int): Number of returned questions (responses).
        es (Elasticsearch): Elasticsearch client instance.

    Returns:
        List[str]: List of contexts (responses) for a given question (query).
    """
    results = es.search(
        index=index_name,
        body={"query": {"match": {"context": question}}},
        size=size,
    )
    return [item["_source"]["context"] for item in results["hits"]["hits"]]


def update_context(
    example: Dict[str, Any], index_name: str, size: int, es: Elasticsearch
) -> Dict[str, Any]:
    """Update context by using get_context helper utility.

    Args:
        example (Dict[str, Any]): Single data instance.
        index_name: Name of the index for retrieving the data.
        size (int): Number of returned questions (queries).
        es (Elasticsearch): Elasticsearch client instance.

    Returns:
        Dict[str, Any]: Single data instance with updated context.
    """
    example["context"] = " ".join(
        get_context(example["question"], index_name, size, es)
    )
    return example


def calculate_element_mrr(
    example: Dict[str, Any], index_name: str, size: int, es: Elasticsearch
) -> Dict[str, Any]:
    """Calculate MRR (Mean Reciprocal Rank) after.

    Args:
        example (Dict[str, Any]): Single data instance.
        index_name (str): Name of the index for retrieving the data.
        size (int): Number of returned questions (queries).
        es (Elasticsearch): Elasticsearch client instance.

    Returns:
        Dict[str, Any]: Single data instance with added MRR value.
    """
    concat_context = get_context(example["question"], index_name, size, es)
    example["mrr"] = (
        1 / (concat_context.index(example["context"]) + 1)
        if example["context"] in concat_context
        else 0
    )
    return example


def get_elastic_search_client(
    cloud_id: str, user: str, password: str
) -> Elasticsearch:
    """Get Elasticsearch client instance.

    Args:
        cloud_id (str): Cloud id of the Elasticsearch cluster.
        user (str): User of the Elasticsearch cluster.
        password (str): Password of the Elasticsearch cluster.

    Returns:
        Elasticsearch: Elasticsearch client instance.
    """

    es = Elasticsearch(cloud_id=cloud_id, http_auth=(user, password))

    return es
