"""Main script for the QA application."""
import logging

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

from src.utils import get_config, get_context, get_elastic_search_client

logger = logging.getLogger(__name__)

es_config = get_config("es_config.ini")
hparams_config = get_config("hparams_config.ini")

es = get_elastic_search_client(
    cloud_id=es_config["ELASTIC"]["cloud_id"],
    user=es_config["ELASTIC"]["user"],
    password=es_config["ELASTIC"]["password"],
)

app = FastAPI()

question_answerer = pipeline(
    "question-answering",
    model=hparams_config["HYPERPARAMS"]["model_checkpoint"],
    device=0 if torch.cuda.is_available() else -1,
    load_in_8bit=True,
)


class QuestionRequest(BaseModel):
    text: str


class Response(BaseModel):
    text: str


@app.on_event("shutdown")
def app_shutdown():
    es.close()


@app.get("/")
def root():
    return Response(
        text="<h1>A self-documenting API for question answering</h1>"
    )


@app.post("/extract")
def extract(body: QuestionRequest):
    # context is to be extracted from ES
    concat_context = " ".join(
        get_context(
            question=body.text,
            index_name=hparams_config["HYPERPARAMS"]["index_name"],
            size=hparams_config["HYPERPARAMS"]["context_size"],
            es=es,
        )
    )
    # For the cases that Elasticsearch returns null
    if not concat_context:
        text = "Answer is not found."
    else:
        result = question_answerer(question=body.text, context=concat_context)

        text = (
            result["answer"]
            if result["score"] > float(hparams_config["HYPERPARAMS"]["qa_threshold"])
            else "Answer is not found."
        )
    return Response(text=text)
