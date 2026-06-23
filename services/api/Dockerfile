# Mosaic API — Hugging Face Spaces (Docker SDK).
#
# The bge-small query embedder runs IN-PROCESS at retrieval time, so we keep
# torch (the decision was: big-RAM free host, no ONNX swap). HF Spaces CPU basic
# gives ~16GB RAM, ample headroom for CPU torch + the 384-dim model.
#
# Build context is services/api (see .dockerignore). HF Spaces routes external
# traffic to the port named by `app_port` in the Space README frontmatter (7860).
FROM python:3.11-slim

WORKDIR /code

# 1) CPU-only torch FIRST, so requirements.txt's sentence-transformers does NOT
#    pull the ~2.5GB CUDA wheel.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2) Python deps as their own cached layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Pre-download the bge-small model at BUILD time so the first live request
#    doesn't pay a ~130MB download. (Torch still loads into RAM on cold start —
#    that's unavoidable; this only removes the network fetch from request #1.)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# 4) Application code (app/, alembic/, alembic.ini, ...).
COPY . .

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
