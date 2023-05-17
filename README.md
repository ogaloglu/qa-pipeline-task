# qa-pipeline-task
## Overview
retriever-reader paradigm
### Model
extractive qa - distilbert fine-tuned on squad
### Dataset
 [Squad Dataset](https://huggingface.co/datasets/squad) 
### Metrics
#### F1
#### Exact Match
#### MRR
#### Latency

## Directory Structure
```bash

├── configs/
│   ├── hparams_config.ini
│   └── es_config_template.ini
├── src/
│   ├── __init__.py
│   ├── evalaute_pipeline.oy
│   ├── main.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_evalaute_pipeline.oy
│   ├── test_main.py
│   └── test_utils.py
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── setup.py
```

## Usage
### Elasticsearch Configureation
The content of the `configs/es_config_template.ini` is as following:
```bash
[ELASTIC]
cloud_id = {INSERT_CLOUDID}
user = {INSERT_USERNAME}
password = {INSERT_PASSWORD}
```
The respective credentials have to be obtained from the author, then the name of the config file has to be changed to `es_config.ini`.
### Running Dokcer Application
Build the docker image
```bash
docker build -t qa-fastapi-demo .
```
Run a container based on the built image
```bash
docker run -d --name app-container -p 80:80 qa-fastapi-demo
```
Connect to SwaggerUI [http://127.0.0.1/docs](http://127.0.0.1/docs) which has a user friendly interface to call and test API directly from browser.

### Evalution Pipeline
First create a conda environment
```bash
conda create -n "venv" python=3.10
```
Then, install the package
```bash
pip install .
```
In order to use evaluation pipeline, squad_dedup_validation.json has to be downloaded. In order to download, run the following command:
```bash
bash download_data.sh
```
Afterwards, in order to evaluate the pipeline run:
```bash
conda create -n "venv" python=3.10
```


### Running Tests
```bash
pytest
```
## Future Work
### Caching
### Inference Monitoring
### ONNX Runtime
### More Tests
### Focus on Reading or Retrieving?
Standalone reader with only one context performs already well.
When the context size get larger, the performance drops with the selected model. Therefore, the focus can be given to keep the reader as is with context size 1, and try out different retrieval paradimgs. MRR could be used as a metric to select a better retriever. Current retriever uses bm25.
### Combining Reader and Retriever Scores
### Evaluate Inference According Threshold



