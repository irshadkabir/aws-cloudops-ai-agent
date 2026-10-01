import json

from tools.aws_tools import (
    list_eks_clusters,
    list_ec2_instances,
    list_cloudwatch_alarms
)


def lambda_handler(event, context):

    print("AWS tool test started")

    tool = event.get("tool")

    # ========================================================
    # EKS
    # ========================================================

    if tool == "list_eks_clusters":

        result = list_eks_clusters()

    # ========================================================
    # EC2
    # ========================================================

    elif tool == "list_ec2_instances":

        result = list_ec2_instances()

    # ========================================================
    # CloudWatch
    # ========================================================

    elif tool == "list_cloudwatch_alarms":

        result = list_cloudwatch_alarms()

    # ========================================================
    # Unknown Tool
    # ========================================================

    else:

        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Unknown or missing tool"
            })
        }

    print(
        "AWS tool result:",
        result
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(result)
    }
