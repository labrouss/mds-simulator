# Multi-stage build: compile the instructor dashboard, then bundle with the simulator

FROM node:20-slim AS dashboard-build
WORKDIR /dashboard
COPY instructor_dashboard/package.json ./
RUN npm install
COPY instructor_dashboard/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mds_sim ./mds_sim
COPY --from=dashboard-build /dashboard/dist ./instructor_dashboard/dist

EXPOSE 2222 8443 8000 9000

CMD ["python", "-m", "mds_sim.main"]
