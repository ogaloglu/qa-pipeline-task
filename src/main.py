"""Main script for the QA application."""
import configparser
import logging
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

from .utils import get_config, get_context, get_es


logging.basicConfig(
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


es_config, hparams_config = get_config("es_config.ini"), get_config("hparams_config.ini")

es = get_es(
    cloud_id=es_config["ELASTIC"]["cloud_id"],
    user=es_config["ELASTIC"]["user"],
    password=es_config["ELASTIC"]["password"],
)

app = FastAPI()

question_answerer = pipeline(
    "question-answering", model=hparams_config["HYPERPARAMS"]["model_checkpoint"]
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
        text="<h1>A self-documenting API to answer a question given to context in an Elastic Search cluster</h1>"
    )


@app.post("/extract")
def predict(body: QuestionRequest):
    # context is to be extracted from ES
    concat_context = " ".join(
        get_context(
            question=body.text,
            index_name=hparams_config["HYPERPARAMS"]["index_name"],
            size=hparams_config["HYPERPARAMS"]["context_size"],
            es=es,
        )
    )
    result = question_answerer(question=body.text, context=concat_context)

    text = (
        result["answer"]
        if result["score"] > float(hparams_config["HYPERPARAMS"]["qa_threshold"])
        else "Answer is not found"
    )
    return Response(text=text)
