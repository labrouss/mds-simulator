FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mds_sim ./mds_sim

EXPOSE 2222 8443 8000 9000

CMD ["python", "-m", "mds_sim.main"]
