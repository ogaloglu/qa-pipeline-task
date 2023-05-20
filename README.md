# QA Pipeline Task
## Overview
A project for a question answering pipeline that can be used via help of a Elasticsearch cluster and FastAPI app.

### Retriever-Reader Paradigm
This project follows the retriever-reader paradigm, which involves retrieving relevant context from an external knowledge base and subsequently processing the retrieved context to extract an answer [[1]](#references).

![qa-png](https://user-images.githubusercontent.com/33498883/239006520-6ea91d0b-20e6-473c-937f-9d32ce5681fa.png)
Retrieved from https://lilianweng.github.io/posts/2020-10-29-odqa/ [[1]](#references).
### Dataset
The utilized dataset for this project is an updated version of the [Squad Dataset](https://huggingface.co/datasets/squad) [[2]](#references). In the original Squad Dataset, the data structure is as follows:
```python
{
    "answers": {
        "answer_start": [1],
        "text": ["This is a test text"]
    },
    "context": "This is a test context.",
    "id": "1",
    "question": "Is this a test?",
    "title": "train test"
}
```
However, the original dataset contains duplicates of the same context, where each duplicate is paired with a different question. To simplify the task, the duplicates of identical contexts have been removed.

The train partition of the dataset serves as the knowledge base for the inference whereas validation partition is used for evaluating the question answering pipeline.
### Reader Model
In this project, extractive question answering formulation is chosen. Accordingly, a
 [distilbert model fine-tuned on squad](https://huggingface.co/distilbert-base-uncased-distilled-squad) [[3]](#references) is ued as the reader model.

### Evaluation Metrics
* End-To-End Pipeline and Only Reader
    * F1
    * Exact Match
* Only Retriever
    * MRR (Mean Reciprocal Rank)

## Project Structure
```bash
qa-pipeline-task/
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
To get started, follow the steps below:

Clone the repository by running the following command:
```bash
git clone https://github.com/ogaloglu/qa-pipeline-task.git
```
Change your current directory to `qa-pipeline-task` using the command:
```bash
cd qa-pipeline-task/
```
### Elasticsearch Configuration
The `configs/es_config_template.ini` file contains the following content:
```bash
[ELASTIC]
cloud_id = {INSERT_CLOUDID}
user = {INSERT_USERNAME}
password = {INSERT_PASSWORD}
```
Obtain the necessary credentials from the [author](mailto:onur.galoglu@gmail.com) and update the values accordingly. Then, rename the file to  `es_config.ini`.

### Hyperparameters Configuration
The `configs/hparams_config.ini` file contains the following default content:
```bash
[HYPERPARAMS]
model_checkpoint = distilbert-base-uncased-distilled-squad
context_size = 2
index_name = squad_dedup_train
qa_threshold = 0.20
```
All keys are required for the inference.
### Running Docker Application
Build the Docker image by executing the following command:
```bash
docker build -t qa-fastapi-demo .
```
Launch a container based on the built image using the command:
```bash
docker run -d --name app-container -p 80:80 qa-fastapi-demo
```
Access the SwaggerUI interface by navigating to [http://127.0.0.1/docs](http://127.0.0.1/docs) in your browser. This interface provides a user-friendly way to call and test the API directly from your browser.

The QA pipeline is designed to provide answers to questions based on the train partition of the [Squad Dataset](https://huggingface.co/datasets/squad).

### Evalution Pipeline
To set up the evaluation pipeline, perform the following steps:

Create a new conda environment. Note that Python version 3.10 or higher is required for `match case` statements. Use the command:
```bash
conda create -n "qa-pipeline-task" python=3.10
```
Activate the conda environment with the following command:
```bash
conda activate qa-pipeline-task
```
Install the package by running:
```bash
pip install -e .
```
To download the `squad_dedup_validation.json` file, which is required for the evaluation pipeline, execute the following command:
```bash
bash download_data.sh
```
Finally, to evaluate the pipeline, run the following command:
```bash
python src/evaluate_pipeline.py\
    --pipeline retrieval\
    --context_size 2\
    --val_set_size 100\
    --dataset_path squad_dedup_validation.json
```

*Key parameters*:
```bash
    --pipeline                   # Selection of the pipeline part to be evaluated. Either retrieval, reader or e2e
    --val_set_size               # Size of the validation set
    --context_size               # Number of contexts (responses) to be retrieved given a question (request)
    --dataset_path                # Path of the validation set to be used for the evaluation
    --index_name                 # Index name of the validation set in the Elasticsearch cluster 
    --model_name                 # Name of the pretrained model to be used for the pipeline

```
### Running Tests
```bash
pytest
```

## Evaluation Results (on Full Validation Set)
* Only Retriever (contetxt_size=1):
    * context_size = 1:
        * MRR: 0.7383
        * Ratio of true first reponse: 73.83%
        * Ratio of uncaptured true answer: 26.17%
    * context_size = 2:
        * MRR: 0.7886
        * Ratio of true first reponse: 73.83%
        * Ratio of uncaptured true answer: 16.11%
    * context_size = 3:
        * MRR: 0.7999
        * Ratio of true first reponse: 73.83%
        * Ratio of uncaptured true answer: 12.72%
    * context_size = 4:
        * MRR: 0.8039
        * Ratio of true first reponse: 73.83%
        * Ratio of uncaptured true answer: 11.13%
    * context_size = 5:
        * MRR: 0.8063
        * Ratio of true first reponse: 73.83%
        * Ratio of uncaptured true answer: 9.92%
* Only Reader:
    * F1: 89.04
    * Exact Match: 82.29
* End-To-End Pipeline:
    * context_size = 1
        * F1: 62.68
        * Exact Match: 68.51
    * context_size = 2
        * F1: 66.02
        * Exact Match: 72.29
    * context_size = 3
        * F1: 60.89
        * Exact Match: 66.85
    * context_size = 4
        * F1: 57.99
        * Exact Match: 64.22
    * context_size = 5
        * F1: 56.00
        * Exact Match: 61.91
### Discussion
The performance of the reader alone represents the upper bound performance for the entire end-to-end pipeline. When we focus solely on the retriever component, we observe a significant decrease in the ratio of uncaptured true answers when the context_size is increased from 1 to 2. However, further increasing the context_size results in only marginal improvements. 

For the end-to-end pipeline, we observe a substantial increase in performance when the context_size is increased from 1 to 2. However, the performance begins to deteriorate as the context_size is further increased. This could be attributed to the increased likelihood of predicting an incorrect span as the answer, even though the decrease in the ratio of uncaptured true answers is minimal as stated previously.

Based on these observations, context_size of 2 is selected as the optimal choice.

## Future Work
### Focus on Reading or Retrieving?
As mentioned earlier, the reader (with the default true context) already performs well. Therefore, the focus can be shifted towards keeping the reader as it is and exploring different retrieval paradigms. Currently, the retriever utilizes the BM25 algorithm, but it would be worthwhile to experiment with dense retrievers such as SentenceTransformers [[4]](#references).
### Splitting Documents into Paragraphs
Following the approach used in BERTserini [[5]](#references), the articles (contexts) can be divided into paragraphs before indexing them. BERTserini demonstrated that paragraph retrieval outperforms article retrieval.
### Combining Reader and Retriever Scores
Similar to BERTserini [[5]](#references), the reader score and the retriever score can be combined via linear interpolation.
### Inference Monitoring
Currently, only the results of the evaluation pipeline are logged. However, it would be beneficial to also log the results of the inference for monitoring purposes. To store a log file, a docker volume needs to be mounted to the application container.
### Threshold for Score during Inference
Score threshold for inference can be tuned based on the desired focus, whether it is on precision or recall.
### Precision and Recall
While exact match and F1 scores are used to evaluate the end-to-end pipeline performance, it could also be worth considering precision or recall to focus specifically on false positives or false negatives.
### More Tests
More unit tests can be implemented, especially for the evaluation pipeline.
### Caching
Respsonses can be cached to a database to decrease latency.
### Docker Image for Elasticsearch
Due to resource limitations on the local machine, it was not possible to run a Docker container of Elasticsearch. Therefore, an Elasticsearch Cloud was used, hosting the cluster there. Alternatively, an Elasticsearch cluster could be created, and docker-compose could be utilized to run both the Elasticsearch container and the app container after establishing a network between them.
### Docker Image Size
The Docker image size currently exceeds 6GB, primarily due to the inclusion of torch and nvidia-cuda libraries.
### ONNX Runtime
The performance of ONNX runtime for inference in terms of latency can be evaluated and compared against the current setup.
### GitHub Actions
GitHub Actions can be utilized for various purposes, such as pushing the Docker image to DockerHub and running tests when changes are committed to the repository.

## References
1. Weng, Lilian. (Oct 2020). How to build an open-domain question answering system? Lil’Log. https://lilianweng.github.io/posts/2020-10-29-odqa/.
2. Rajpurkar, P., Zhang, J., Lopyrev, K., & Liang, P. (2016). SQuAD: 100,000+ Questions for Machine Comprehension of Text. arXiv e-prints, arXiv:1606.05250.
3. Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. In NeurIPS EMC^2 Workshop.
4. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics.
5. Yang, W., Xie, Y., Lin, A., Li, X., Tan, L., Xiong, K., Li, M., & Lin, J. (2019). End-to-end open-domain question answering with bertserini. arXiv preprint arXiv:1902.01718.


