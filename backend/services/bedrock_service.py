import boto3

REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-micro-v1:0"

client = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


def ask_bedrock(message: str) -> str:
    response = client.converse(
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

    return answer
