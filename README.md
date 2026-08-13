# Car Assistant

**AI-powered car maintenance assistant** — a serverless FastAPI backend that lets a driver log maintenance notes by text or voice, transcribes voice notes automatically, and answers car-specific questions using Claude with the car's history as context.

## How it works

1. The user records a voice note ("I just changed the oil at 85,000 km")
2. The API issues a presigned S3 URL; the audio is uploaded directly to S3
3. AWS Transcribe converts speech to text as an async job with status polling
4. The note is stored in PostgreSQL, linked to the user's car
5. When the user asks a question, Claude (Anthropic API) responds as a mechanic assistant, with the car's model and past maintenance notes injected as context

## Architecture

```
Client ──> API Gateway ──> Lambda (FastAPI via Mangum)
                              │
              ┌───────────────┼─────────────────┐
              ▼               ▼                 ▼
        RDS PostgreSQL    S3 (voice notes)   Anthropic API
         (private VPC)        │
                              ▼
                        AWS Transcribe
```

All infrastructure is defined in **Terraform**: VPC with private subnets, RDS PostgreSQL, Lambda, S3 with lifecycle rules, IAM policies, and a bastion host for database access during development.

## Tech stack

**Backend**
- Python, FastAPI, Pydantic models
- Mangum (ASGI adapter for AWS Lambda)
- Anthropic API (Claude) for context-aware responses
- psycopg2 / PostgreSQL

**Infrastructure (Terraform)**
- AWS Lambda + API Gateway (serverless deployment)
- RDS PostgreSQL in private subnets
- S3 for audio storage (presigned uploads, lifecycle policies)
- AWS Transcribe for speech-to-text
- Bastion host with Elastic IP for dev database access

## API overview

| Area | Endpoints |
|---|---|
| Health | `GET /health` |
| Users & cars | create user, create car, list cars |
| Notes | create text note, list notes per car |
| Voice notes | request presigned upload URL, start transcription, poll transcription status |
| AI assistant | ask a question about the car with maintenance history as context |

Interactive docs available at `/docs` (Swagger UI) when running locally.

## Run locally

1. Create a `.env` in `backend/` (never commit it):
   ```
   DB_HOST=...
   DB_PORT=5432
   DB_NAME=...
   DB_USER=...
   DB_PASSWORD=...
   ANTHROPIC_API_KEY=...
   AWS_REGION=...
   ```
2. Install and run:
   ```
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. Open http://localhost:8000/docs

## Deploy

```
cd infrastructure
terraform init
terraform plan
terraform apply
```

Lambda deployment packages are built outside the repository tree — build artifacts and dependency directories are intentionally not version-controlled.
