import os
import boto3
from botocore.exceptions import ClientError


REGION = os.environ.get(
    "AWS_REGION",
    "us-east-1"
)


# ============================================================
# AWS Clients
# ============================================================

eks_client = boto3.client(
    "eks",
    region_name=REGION
)

ec2_client = boto3.client(
    "ec2",
    region_name=REGION
)

cloudwatch_client = boto3.client(
    "cloudwatch",
    region_name=REGION
)


# ============================================================
# Helper: AWS Error Response
# ============================================================

def build_error_response(error):
    """
    Convert an AWS ClientError into a consistent tool response.
    """

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

    return {
        "success": False,
        "error_code": error_code,
        "error_message": error_message
    }


# ============================================================
# Tool 1: List EKS Clusters
# ============================================================

def list_eks_clusters():
    """
    Return EKS clusters available in the configured AWS region.

    Read-only operation.
    """

    try:

        response = eks_client.list_clusters()

        clusters = response.get(
            "clusters",
            []
        )

        return {
            "success": True,
            "region": REGION,
            "clusters": clusters,
            "count": len(clusters)
        }

    except ClientError as error:

        return build_error_response(error)


# ============================================================
# Tool 2: List EC2 Instances
# ============================================================

def list_ec2_instances():
    """
    Return basic information about EC2 instances in the
    configured AWS region.

    Read-only operation.
    """

    try:

        response = ec2_client.describe_instances()

        instances = []

        for reservation in response.get(
            "Reservations",
            []
        ):

            for instance in reservation.get(
                "Instances",
                []
            ):

                instance_name = None

                for tag in instance.get("Tags", []):

                    if tag.get("Key") == "Name":
                        instance_name = tag.get("Value")
                        break

                instances.append(
                    {
                        "instance_id": instance.get(
                            "InstanceId"
                        ),
                        "name": instance_name,
                        "instance_type": instance.get(
                            "InstanceType"
                        ),
                        "state": instance.get(
                            "State",
                            {}
                        ).get(
                            "Name"
                        ),
                        "private_ip": instance.get(
                            "PrivateIpAddress"
                        ),
                        "public_ip": instance.get(
                            "PublicIpAddress"
                        )
                    }
                )

        return {
            "success": True,
            "region": REGION,
            "instances": instances,
            "count": len(instances)
        }

    except ClientError as error:

        return build_error_response(error)


# ============================================================
# Tool 3: List CloudWatch Alarms
# ============================================================

def list_cloudwatch_alarms():
    """
    Return CloudWatch metric alarms in the configured
    AWS region.

    Read-only operation.
    """

    try:

        response = cloudwatch_client.describe_alarms()

        alarms = []

        for alarm in response.get(
            "MetricAlarms",
            []
        ):

            alarms.append(
                {
                    "alarm_name": alarm.get(
                        "AlarmName"
                    ),
                    "state": alarm.get(
                        "StateValue"
                    ),
                    "metric_name": alarm.get(
                        "MetricName"
                    ),
                    "namespace": alarm.get(
                        "Namespace"
                    )
                }
            )

        return {
            "success": True,
            "region": REGION,
            "alarms": alarms,
            "count": len(alarms)
        }

    except ClientError as error:

        return build_error_response(error)
