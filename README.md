# qa-pipeline-task
## Overview



### Retriever Reader Paradigm

![qa-png](https://user-images.githubusercontent.com/33498883/239006520-6ea91d0b-20e6-473c-937f-9d32ce5681fa.png)
[1] https://lilianweng.github.io/posts/2020-10-29-odqa/
### Dataset
 [Squad Dataset](https://huggingface.co/datasets/squad) 
### Model
extractive qa - 

 [distilbert fine-tuned on squad](https://huggingface.co/distilbert-base-uncased-distilled-squad) 

### Evaluation Metrics
* End-To-End Pipeline and Standalone Reader
    * F1
    * Exact Match
    * Latency
* Standalone Retriever
    * MRR


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
Afterwards, in order to evaluate the pipeline, run:
```bash
python src/evaluate_pipeline.py\
    --pipeline retrieval\
    --context_size 1\
    --val_set_size 1000\
    --dataset_path squad_dedup_validation.json
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

## References
1. Weng, Lilian. (Oct 2020). How to build an open-domain question answering system? Lil’Log. https://lilianweng.github.io/posts/2020-10-29-odqa/.
2. Rajpurkar, P., Zhang, J., Lopyrev, K., & Liang, P. (2016). SQuAD: 100,000+ Questions for Machine Comprehension of Text. arXiv e-prints, arXiv:1606.05250.
3. Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. In NeurIPS EMC^2 Workshop.


