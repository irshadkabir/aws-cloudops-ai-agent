import boto3

# AWS Region where we are using Amazon Bedrock
REGION = "us-east-1"

# Bedrock inference profile for Amazon Nova Micro
MODEL_ID = "us.amazon.nova-micro-v1:0"

# Create the Bedrock Runtime client
client = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)

# Send a message to the foundation model
response = client.converse(
    modelId=MODEL_ID,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": "Explain why an EKS node can become NotReady."
                }
            ]
        }
    ]
)

# Extract the model's text response
answer = response["output"]["message"]["content"][0]["text"]

print("\nCloudOps AI Response:\n")
print(answer)
