FROM python:3.10-slim
WORKDIR /function
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY handler.py .
ENV fprocess="python3 handler.py"
CMD ["python3", "handler.py"] 