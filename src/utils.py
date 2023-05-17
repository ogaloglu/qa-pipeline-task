"""Utility functions."""
import configparser
from pathlib import Path
from typing import Any, Dict, List

from elasticsearch import Elasticsearch


def get_config(name: str) -> configparser.ConfigParser:
    """Read the respective config.ini file and return a config object.

    Args:
        name (str): Name of the config within configs directory

    Returns:
        configparser.ConfigParser: Config object
    """
    config = configparser.ConfigParser()
    with open(Path(__file__).parent / ".." / f"configs/{name}") as f:
        config.read_file(f)
    return config


def get_context(
    question: str, index_name: str, size: int, es: Elasticsearch
) -> List[str]:
    """Retrieve the list of the most relevant contexts given a question from
    Elasticsearch cluster.

    Args:
        question (str): Question that used as the query
        index_name (str): Name of the index for retrieving the data
        size (int): Number of returned questions (responses)
        es (Elasticsearch): Elasticsearch client instance

    Returns:
        List[str]: List of contexts (responses) for a given question (query)
    """
    res = es.search(
        index=index_name,
        body={"query": {"match": {"context": question}}},
        size=size
    )
    # TODO: add retrieval scores
    return [i["_source"]["context"] for i in res["hits"]["hits"]]


def update_context(
    example: Dict[str, Any], index_name: str, size: int, es: Elasticsearch
) -> Dict[str, Any]:
    """Update context by using get_context helper utility.

    Args:
        example (Dict[str, Any]): Single data instance
        index_name: Name of the index for retrieving the data
        size (int): Number of returned questions (queries)
        es (Elasticsearch): Elasticsearch client instance

    Returns:
        Dict[str, Any]: Single data instance with updated context
    """
    example["context"] = " ".join(
        get_context(example["question"], index_name, size, es)
    )
    return example


def calculate_element_mrr(
    example: Dict[str, Any], index_name: str, size: int, es: Elasticsearch
) -> Dict[str, Any]:
    """Calculate MRR after.

    Args:
        example (Dict[str, Any]): Single data instance
        index_name (str): Name of the index for retrieving the data
        size (int): Number of returned questions (queries)
        es (Elasticsearch): Elasticsearch client instance

    Returns:
        Dict[str, Any]: Single data instance with added MRR value
    """
    concat_context = get_context(example["question"], index_name, size, es)
    example["mrr"] = (
        1 / (concat_context.index(example["context"]) + 1)
        if example["context"] in concat_context
        else 0
    )
    return example


def get_es(cloud_id: str, user: str, password: str) -> Elasticsearch:
    """Get Elasticsearch client instance.

    Args:
        cloud_id (str): Cloud id of the Elasticsearch cluster
        user (str): User of the Elasticsearch cluster
        password (str): Password of the Elasticsearch cluster

    Returns:
        Elasticsearch: Elasticsearch client instance
    """

    es = Elasticsearch(cloud_id=cloud_id, http_auth=(user, password))

    return es
