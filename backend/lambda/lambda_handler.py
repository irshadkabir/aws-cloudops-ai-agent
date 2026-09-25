import json
import boto3

from datetime import datetime, timezone
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


# ============================================================
# Configuration
# ============================================================

REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-micro-v1:0"
TABLE_NAME = "cloudops-ai-agent-conversations-dev"
HISTORY_LIMIT = 10


# ============================================================
# AWS Clients / Resources
# ============================================================

# Amazon Bedrock Runtime client
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


# DynamoDB resource
dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION
)


# DynamoDB conversation table
table = dynamodb.Table(TABLE_NAME)


# ============================================================
# Lambda Handler
# ============================================================

def lambda_handler(event, context):

    print("Lambda request received")

    # --------------------------------------------------------
    # 1. Extract request data
    # --------------------------------------------------------

    # Request coming from API Gateway
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

    # Direct Lambda test event
    else:

        session_id = event.get("session_id")
        message = event.get("message")

    # --------------------------------------------------------
    # 2. Validate session_id
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
    # 3. Validate message
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

    # --------------------------------------------------------
    # 4. Process request
    # --------------------------------------------------------

    try:

        # ----------------------------------------------------
        # 5. Retrieve previous conversation history
        # ----------------------------------------------------

        history_response = table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=False,
            Limit=HISTORY_LIMIT
        )

        history_items = history_response.get("Items", [])

        # DynamoDB returned newest -> oldest.
        # Bedrock needs oldest -> newest.
        history_items.reverse()

        print(
            "Conversation history retrieved:",
            len(history_items),
            "interaction(s)"
        )

        # ----------------------------------------------------
        # 6. Convert DynamoDB history into Bedrock messages
        # ----------------------------------------------------

        messages = []

        for item in history_items:

            question = item.get("question")
            previous_answer = item.get("answer")

            if question and previous_answer:

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": question
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

        # ----------------------------------------------------
        # 7. Add current user message
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "text": message
                    }
                ]
            }
        )

        # ----------------------------------------------------
        # 8. Send conversation to Amazon Bedrock
        # ----------------------------------------------------

        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages
        )

        # ----------------------------------------------------
        # 9. Extract AI response
        # ----------------------------------------------------

        answer = response["output"]["message"]["content"][0]["text"]

        # ----------------------------------------------------
        # 10. Generate UTC timestamp
        # ----------------------------------------------------

        timestamp = datetime.now(timezone.utc).isoformat()

        # ----------------------------------------------------
        # 11. Store new conversation in DynamoDB
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 12. Return successful response
        # ----------------------------------------------------

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "session_id": session_id,
                "answer": answer
            })
        }

    # --------------------------------------------------------
    # 13. Handle AWS service errors
    # --------------------------------------------------------

    except ClientError as error:

        error_code = error.response["Error"]["Code"]

        print(
            "AWS ClientError:",
            error_code
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

    # --------------------------------------------------------
    # 14. Handle unexpected errors
    # --------------------------------------------------------

    except Exception as error:

        print(
            "Unexpected error:",
            type(error).__name__
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
