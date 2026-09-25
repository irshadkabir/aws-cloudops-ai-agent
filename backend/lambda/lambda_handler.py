import json
import boto3
from botocore.exceptions import ClientError


# AWS configuration
REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-micro-v1:0"


# Create Bedrock Runtime client
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def lambda_handler(event, context):

    print("Lambda request received")

    # -----------------------------------------
    # 1. Extract message from incoming request
    # -----------------------------------------

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

        message = body.get("message")

    # Direct Lambda test event
    else:
        message = event.get("message")

    # -----------------------------------------
    # 2. Validate message
    # -----------------------------------------

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

    # -----------------------------------------
    # 3. Send message to Amazon Bedrock
    # -----------------------------------------

    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": message
                        }
                    ]
                }
            ]
        )

        # -----------------------------------------
        # 4. Extract AI response
        # -----------------------------------------

        answer = response["output"]["message"]["content"][0]["text"]

        # -----------------------------------------
        # 5. Return successful response
        # -----------------------------------------

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "answer": answer
            })
        }

    # -----------------------------------------
    # 6. Handle AWS / Bedrock errors
    # -----------------------------------------

    except ClientError as error:

        print(
            "Bedrock ClientError:",
            error.response["Error"]["Code"]
        )

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Unable to generate AI response"
            })
        }

    # -----------------------------------------
    # 7. Handle unexpected errors
    # -----------------------------------------

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
