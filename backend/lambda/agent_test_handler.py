import json

from agent.tool_agent import run_agent


def lambda_handler(event, context):

    print("Nova tool-use agent test started")

    message = event.get("message")

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

    result = run_agent(
        message
    )

    status_code = (
        200
        if result.get("success")
        else 500
    )

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(
            result
        )
    }
