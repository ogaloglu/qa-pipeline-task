FROM python:3.10.6

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

COPY setup.py /code

RUN pip install -e .

COPY ./configs /code/configs

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]