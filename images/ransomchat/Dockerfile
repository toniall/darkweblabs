# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# RansomChat — helpdesk-style negotiation training simulator (Chapter 12).
# Flask only; the operator's HTTP calls to OpenAI/Grok/Ollama use the stdlib.
# The negotiations.db is mounted read-only at runtime (single source of truth
# in labs/artifacts/ransomchat/), so it is not copied into the image.
FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py session.py chat.html /app/
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=4s --retries=5 \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health',timeout=3).status==200 else 1)"
CMD ["python3", "app.py"]
