import json
import os
import boto3
import botocore

from datetime import datetime, timezone
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


# ============================================================
# 1. Configuration
# ============================================================

REGION = "us-east-1"

MODEL_ID = "us.amazon.nova-micro-v1:0"

TABLE_NAME = "cloudops-ai-agent-conversations-dev"

HISTORY_LIMIT = 10

KNOWLEDGE_BASE_RESULTS = 3

# Knowledge Base ID comes from Lambda environment variables.
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID")


# ============================================================
# 2. AWS Clients / Resources
# ============================================================

# Bedrock Runtime:
# Used to invoke Amazon Nova Micro.
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


# Bedrock Agent Runtime:
# Used to query the Bedrock Knowledge Base.
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


# DynamoDB resource:
# Used for conversation memory.
dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION
)


table = dynamodb.Table(TABLE_NAME)


# ============================================================
# 3. Helper Function - Retrieve Knowledge
# ============================================================

def retrieve_knowledge(query):
    """
    Retrieve relevant CloudOps documentation from the
    Amazon Bedrock Managed Knowledge Base.
    """

    if not KNOWLEDGE_BASE_ID:
        raise ValueError(
            "KNOWLEDGE_BASE_ID environment variable is not configured"
        )

    print("Searching CloudOps Knowledge Base")

    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={
            "text": query
        },
        retrievalConfiguration={
            "managedSearchConfiguration": {
                "numberOfResults": KNOWLEDGE_BASE_RESULTS
            }
        }
    )

    retrieval_results = response.get(
        "retrievalResults",
        []
    )

    print(
        "Knowledge Base results retrieved:",
        len(retrieval_results)
    )

    retrieved_chunks = []
    sources = []

    for result in retrieval_results:

        # ----------------------------------------------------
        # Extract retrieved text
        # ----------------------------------------------------

        content = result.get(
            "content",
            {}
        )

        text = content.get("text")

        if text:
            retrieved_chunks.append(text)

        # ----------------------------------------------------
        # Extract S3 source if available
        # ----------------------------------------------------

        location = result.get(
            "location",
            {}
        )

        s3_location = location.get(
            "s3Location",
            {}
        )

        uri = s3_location.get("uri")

        if uri and uri not in sources:
            sources.append(uri)

    # Combine all retrieved chunks into one context block.
    knowledge_context = "\n\n".join(
        retrieved_chunks
    )

    return knowledge_context, sources


# ============================================================
# 4. Lambda Handler
# ============================================================

def lambda_handler(event, context):

    print("Lambda request received")

    # These two lines are temporary but useful while we
    # troubleshoot the managed Knowledge Base SDK support.
    print("Boto3 version:", boto3.__version__)
    print("Botocore version:", botocore.__version__)

    # --------------------------------------------------------
    # 5. Extract request
    # --------------------------------------------------------

    if "body" in event:

        try:
            body = json.loads(event["body"])

        except (json.JSONDecodeError, TypeError):

            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "Invalid JSON request body"
                })
            }

        session_id = body.get("session_id")
        message = body.get("message")

    else:

        session_id = event.get("session_id")
        message = event.get("message")

    # --------------------------------------------------------
    # 6. Validate session_id
    # --------------------------------------------------------

    if not session_id:

        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "session_id is required"
            })
        }

    # --------------------------------------------------------
    # 7. Validate message
    # --------------------------------------------------------

    if not message:

        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "message is required"
            })
        }

    try:

        # ====================================================
        # 8. Retrieve Conversation History
        # ====================================================

        history_response = table.query(
            KeyConditionExpression=Key(
                "session_id"
            ).eq(session_id),
            ScanIndexForward=False,
            Limit=HISTORY_LIMIT
        )

        history_items = history_response.get(
            "Items",
            []
        )

        # DynamoDB returns newest -> oldest.
        # Reverse so Nova receives oldest -> newest.
        history_items.reverse()

        print(
            "Conversation history retrieved:",
            len(history_items),
            "interaction(s)"
        )

        # ====================================================
        # 9. Retrieve Knowledge Base Context
        # ====================================================

        knowledge_context, sources = retrieve_knowledge(
            message
        )

        # ====================================================
        # 10. Build Conversation History
        # ====================================================

        messages = []

        for item in history_items:

            previous_question = item.get(
                "question"
            )

            previous_answer = item.get(
                "answer"
            )

            if previous_question and previous_answer:

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": previous_question
                            }
                        ]
                    }
                )

                messages.append(
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "text": previous_answer
                            }
                        ]
                    }
                )

        # ====================================================
        # 11. Build RAG / Grounding Prompt
        # ====================================================

        if knowledge_context:

            grounded_message = f"""
You are a CloudOps AI assistant.

Use the supplied CloudOps knowledge when it is relevant
to the user's question.

Do not invent organization-specific procedures, policies,
maintenance windows, commands, escalation requirements,
or operational standards that are not supported by the
supplied CloudOps knowledge.

If the user specifically asks about internal CloudOps
documentation and the required information is not present
in the supplied knowledge, clearly state that the
information was not found in the available CloudOps
knowledge.

CloudOps knowledge:

{knowledge_context}

User question:

{message}
"""

        else:

            grounded_message = f"""
You are a CloudOps AI assistant.

No relevant CloudOps knowledge was retrieved for this
request.

You may answer general AWS, Kubernetes, DevOps, Linux,
cloud, or infrastructure questions using your general
technical knowledge.

However, do not invent organization-specific procedures,
policies, maintenance windows, commands, escalation
requirements, or operational standards.

If the user specifically asks about internal CloudOps
documentation, state that the requested information was
not found in the available CloudOps knowledge.

User question:

{message}
"""

        # Add current question with retrieved context.
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "text": grounded_message
                    }
                ]
            }
        )

        # ====================================================
        # 12. Invoke Nova Micro
        # ====================================================

        print("Invoking Nova Micro")

        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages
        )

        # ====================================================
        # 13. Extract AI Answer
        # ====================================================

        answer = (
            response["output"]
            ["message"]
            ["content"][0]
            ["text"]
        )

        print("AI response generated successfully")

        # ====================================================
        # 14. Generate Timestamp
        # ====================================================

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        # ====================================================
        # 15. Store Conversation in DynamoDB
        # ====================================================

        table.put_item(
            Item={
                "session_id": session_id,
                "timestamp": timestamp,
                "question": message,
                "answer": answer,
                "model_id": MODEL_ID
            }
        )

        print("Conversation stored successfully")

        # ====================================================
        # 16. Return Successful Response
        # ====================================================

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "session_id": session_id,
                "answer": answer,
                "sources": sources
            })
        }

    # ========================================================
    # 17. AWS Service Errors
    # ========================================================

    except ClientError as error:

        error_code = error.response[
            "Error"
        ].get(
            "Code",
            "UnknownAWSClientError"
        )

        error_message = error.response[
            "Error"
        ].get(
            "Message",
            "No AWS error message provided"
        )

        print(
            "AWS ClientError:",
            error_code,
            "-",
            error_message
        )

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Unable to process request"
            })
        }

    # ========================================================
    # 18. Unexpected Errors
    # ========================================================

    except Exception as error:

        print(
            "Unexpected error:",
            type(error).__name__,
            str(error)
        )

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Internal server error"
            })
        }
