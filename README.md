# CloudOps AI Agent

CloudOps AI Agent is a hands-on project for building an AI-powered cloud operations assistant on AWS.

The project is being developed incrementally, starting with Amazon Bedrock integration and a Python/FastAPI backend, and will later incorporate AWS infrastructure, observability, knowledge retrieval, agent tools, security, Infrastructure as Code, and CI/CD.

## Current Architecture

Client
  |
  v
FastAPI
  |
  v
Python / Boto3
  |
  v
Amazon Bedrock
  |
  v
Amazon Nova Micro

## Current Features

- Amazon Bedrock integration
- Amazon Nova Micro inference
- Python Boto3 integration
- FastAPI backend
- Health endpoint
- Chat endpoint

## API Endpoints

### Health

GET /health

### Chat

POST /chat

Example request:

```json
{
  "message": "Why can an EKS node become NotReady?"
}
