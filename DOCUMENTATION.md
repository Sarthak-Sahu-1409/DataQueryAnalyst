# Data Query Assistant - Technical Documentation

## Overview
Data Query Assistant is a full-stack application that lets users analyze CSV datasets using natural language. The backend uses FastAPI and Google Gemini (via LangChain) to generate Python code, executes that code, and returns results and optional visualizations. Uploaded CSVs and generated images are stored in AWS S3 under session-specific prefixes.

## Architecture
- Frontend: React (Vite) SPA with drag-and-drop CSV upload and a query UI.
- Backend: FastAPI service exposing endpoints for upload, analysis, session cleanup, and image retrieval.
- LLM: Google Gemini for code generation, integrated through LangChain.
- Execution: Generated Python code executed in a controlled environment; stdout/stderr captured.
- Storage: AWS S3 (boto3). Objects are saved as `sessions/{session_id}/...`.

## Repository Structure
```
backend/
  main.py                 # FastAPI app and endpoints
  utils/
    llmhandler.py         # LLM prompt + code generation
    processdata.py        # CSV metadata + sample extraction
    pythonexecutor.py     # Run generated Python code
  pyproject.toml          # Poetry dependencies
  poetry.lock
frontend/
  csv-analyzer-ui/        # React app (Vite)
README.md                 # Project quickstart
DOCUMENTATION.md          # This document
```

## Prerequisites
- Python 3.12+
- Node.js 18+
- Google Gemini API key
- AWS account with an S3 bucket

## Configuration
Create a `.env` file in the `backend/` directory or provide these as environment variables:
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=your_aws_region            # e.g., us-east-1
S3_BUCKET_NAME=your_bucket_name       # existing bucket
```
Notes:
- boto3 uses the default AWS credential chain. You may use IAM roles, AWS profiles, or environment variables.
- Ensure the principal has `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, and `s3:ListBucket` permissions on the bucket.

## Installation
Backend:
```
cd backend
pip install poetry
poetry install
poetry shell
```
Frontend:
```
cd frontend/csv-analyzer-ui
npm install
```

## Running
Backend:
```
cd backend
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Frontend:
```
cd frontend/csv-analyzer-ui
npm run dev
```

## Data Flow
1. User uploads a CSV via the frontend.
2. Backend streams the file to S3 at `sessions/{session_id}/{file_name}` and returns `session_id`.
3. User submits a natural language query with `session_id`.
4. Backend locates the CSV in S3, downloads it to a temp path, extracts metadata/sample, requests code from the LLM, then executes that code.
5. If a visualization is generated, the image is uploaded to S3 as `sessions/{session_id}/output_{timestamp}.png`.

## API Reference
Base URL: `http://localhost:8000`

### POST /upload/
- Description: Upload a CSV; store it in S3; return session info.
- Request: multipart/form-data with `file`.
- Response 200:
```
{
  "session_id": "<uuid>",
  "file_name": "<original.csv>"
}
```
Example:
```
curl -X POST \
  -F "file=@/path/to/data.csv" \
  http://localhost:8000/upload/
```

### POST /analyze/
- Description: Analyze the uploaded CSV using a natural language prompt.
- Request: multipart/form-data
  - `session_id` (string, required)
  - `user_query` (string, required)
- Response 200:
```
{
  "metadata_and_sample": { ... },
  "generated_code": "<python code>",
  "stdout": "...",
  "stderr": "...",
  "flags": { ... },
  "image_key": "sessions/{session_id}/output_{timestamp}.png" | null,
  "image_timestamp": "YYYYMMDDHHMMSS" | null
}
```
Example:
```
curl -X POST \
  -F "session_id=<uuid-from-upload>" \
  -F "user_query=Show average price by category" \
  http://localhost:8000/analyze/
```

### POST /clear_session/
- Description: Delete all S3 objects under `sessions/{session_id}/`.
- Request: multipart/form-data with `session_id`.
- Response 200:
```
{ "status": "session cleared" }
```
Example:
```
curl -X POST -F "session_id=<uuid>" http://localhost:8000/clear_session/
```

### GET /get_image/
- Description: Download a generated image via the backend.
- Query params:
  - `session_id` (string, required)
  - `timestamp` (YYYYMMDDHHMMSS, required)
- Response 200: image/png; 404 if missing
Example:
```
curl -G \
  --data-urlencode "session_id=<uuid>" \
  --data-urlencode "timestamp=<YYYYMMDDHHMMSS>" \
  http://localhost:8000/get_image/ --output output.png
```

## Security and Permissions
- Prefer least-privilege IAM policies scoped to the target bucket/prefix.
- Consider request size limits and validation for uploads.
- Avoid long-lived static AWS keys in production; prefer roles and secret managers.

## Error Handling
- Upload errors: 4xx for invalid input; 5xx for S3 or server failures.
- Analyze errors: 404 if session file missing; `stderr` surfaces code execution issues.
- Image retrieval: 404 when the specified image does not exist.

## Frontend Notes
- Development expects backend at `http://localhost:8000`.
- Upload must be `multipart/form-data` with field name `file`.
- When `image_key` and `image_timestamp` are returned, call `/get_image` to display the chart.

## Deployment
- Containerize the backend and front it with a reverse proxy (TLS enabled).
- Configure env via a secrets manager (AWS SSM/Secrets Manager) in production.
- Attach an IAM role to compute (ECS/EKS/EC2/Lambda) for S3 access.
- Build frontend (`npm run build`) and deploy to static hosting/CDN.

## Troubleshooting
- S3 AccessDenied: verify credentials/role, bucket policy, and region.
- Missing S3 bucket: create the bucket in `AWS_REGION`; set `S3_BUCKET_NAME`.
- LLM failures: validate `GOOGLE_API_KEY` and service quotas.
- Empty/incorrect results: inspect `stdout`/`stderr` and the generated code in the response.
- Large files: consider multipart upload and server/proxy body size limits.

