import json
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-micro-v1:0"

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def lambda_handler(event, context):

    print("Lambda request received")

    message = event.get("message")

    if not message:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "message is required"
            })
        }

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

        answer = response["output"]["message"]["content"][0]["text"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "answer": answer
            })
        }

    except ClientError as error:

        print(
            "Bedrock ClientError:",
            error.response["Error"]["Code"]
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Unable to generate AI response"
            })
        }

    except Exception as error:

        print(
            "Unexpected error:",
            type(error).__name__
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error"
            })
        }
