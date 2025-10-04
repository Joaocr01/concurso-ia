FROM python:3.11-slim
WORKDIR /worker
COPY requirements.txt /worker/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY worker.py /worker/worker.py
COPY prompts /worker/prompts
ENV PYTHONUNBUFFERED=1
CMD ["python", "worker.py"]