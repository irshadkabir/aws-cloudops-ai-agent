import os
import boto3
import time
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

logs_client = boto3.client(
    "logs",
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
def get_eks_cluster_details(cluster_name):
    """
    Return operational details for a specific EKS cluster.

    This tool is read-only and uses the EKS DescribeCluster API.
    """

    try:
        if not cluster_name:
            return {
                "success": False,
                "error": "cluster_name is required"
            }

        response = eks_client.describe_cluster(
            name=cluster_name
        )

        cluster = response.get("cluster", {})
        vpc_config = cluster.get("resourcesVpcConfig", {})
        logging_config = cluster.get("logging", {})

        return {
            "success": True,
            "cluster": {
                "name": cluster.get("name"),
                "status": cluster.get("status"),
                "version": cluster.get("version"),
                "platform_version": cluster.get("platformVersion"),
                "endpoint": cluster.get("endpoint"),
                "role_arn": cluster.get("roleArn"),
                "vpc_id": vpc_config.get("vpcId"),
                "subnet_ids": vpc_config.get("subnetIds", []),
                "security_group_ids": vpc_config.get(
                    "securityGroupIds",
                    []
                ),
                "cluster_security_group_id": vpc_config.get(
                    "clusterSecurityGroupId"
                ),
                "endpoint_public_access": vpc_config.get(
                    "endpointPublicAccess"
                ),
                "endpoint_private_access": vpc_config.get(
                    "endpointPrivateAccess"
                ),
                "public_access_cidrs": vpc_config.get(
                    "publicAccessCidrs",
                    []
                ),
                "logging": logging_config
            }
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def list_eks_nodegroups(cluster_name):
    """
    List managed node groups for a specific EKS cluster.

    This tool is read-only and uses the EKS ListNodegroups API.
    """

    try:
        if not cluster_name:
            return {
                "success": False,
                "error": "cluster_name is required"
            }

        nodegroups = []
        next_token = None

        while True:
            request = {
                "clusterName": cluster_name
            }

            if next_token:
                request["nextToken"] = next_token

            response = eks_client.list_nodegroups(**request)

            nodegroups.extend(
                response.get("nodegroups", [])
            )

            next_token = response.get("nextToken")

            if not next_token:
                break

        return {
            "success": True,
            "region": REGION,
            "cluster_name": cluster_name,
            "nodegroups": nodegroups,
            "count": len(nodegroups)
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def get_eks_nodegroup_details(cluster_name, nodegroup_name):
    """
    Return operational details for a specific EKS managed node group.

    This tool is read-only and uses the EKS DescribeNodegroup API.
    """

    try:
        if not cluster_name:
            return {
                "success": False,
                "error": "cluster_name is required"
            }

        if not nodegroup_name:
            return {
                "success": False,
                "error": "nodegroup_name is required"
            }

        response = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup_name
        )

        nodegroup = response.get("nodegroup", {})
        scaling = nodegroup.get("scalingConfig", {})
        health = nodegroup.get("health", {})

        health_issues = []

        for issue in health.get("issues", []):
            health_issues.append({
                "code": issue.get("code"),
                "message": issue.get("message"),
                "resource_ids": issue.get("resourceIds", [])
            })

        return {
            "success": True,
            "region": REGION,
            "nodegroup": {
                "cluster_name": nodegroup.get("clusterName"),
                "nodegroup_name": nodegroup.get("nodegroupName"),
                "status": nodegroup.get("status"),
                "version": nodegroup.get("version"),
                "release_version": nodegroup.get("releaseVersion"),
                "ami_type": nodegroup.get("amiType"),
                "capacity_type": nodegroup.get("capacityType"),
                "instance_types": nodegroup.get("instanceTypes", []),
                "scaling": {
                    "min_size": scaling.get("minSize"),
                    "max_size": scaling.get("maxSize"),
                    "desired_size": scaling.get("desiredSize")
                },
                "health_issues": health_issues
            }
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def list_cloudwatch_log_groups():
    """
    List CloudWatch Logs log groups in the configured AWS region.

    This tool is read-only and uses the DescribeLogGroups API.
    """

    try:
        log_groups = []
        next_token = None

        while True:
            request = {}

            if next_token:
                request["nextToken"] = next_token

            response = logs_client.describe_log_groups(**request)

            for log_group in response.get("logGroups", []):
                log_groups.append({
                    "log_group_name": log_group.get("logGroupName"),
                    "retention_days": log_group.get("retentionInDays"),
                    "stored_bytes": log_group.get("storedBytes", 0)
                })

            next_token = response.get("nextToken")

            if not next_token:
                break

        return {
            "success": True,
            "region": REGION,
            "log_groups": log_groups,
            "count": len(log_groups)
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def get_recent_log_events(
    log_group_name,
    minutes=30,
    filter_pattern=None,
    limit=50
):
    """
    Retrieve recent events from a CloudWatch Logs log group.

    Parameters:
        log_group_name: CloudWatch Logs log group name.
        minutes: How far back to search. Default: 30 minutes.
        filter_pattern: Optional CloudWatch Logs filter pattern.
        limit: Maximum number of events to return. Default: 50.

    This tool is read-only and uses the FilterLogEvents API.
    """

    if not log_group_name:
        return {
            "success": False,
            "error": "ValidationError",
            "message": "log_group_name is required"
        }

    try:
        # Prevent excessively large requests.
        minutes = int(minutes)
        limit = int(limit)

        if minutes < 1:
            minutes = 1

        if minutes > 1440:
            minutes = 1440

        if limit < 1:
            limit = 1

        if limit > 100:
            limit = 100

        # CloudWatch Logs expects epoch time in milliseconds.
        end_time = int(time.time() * 1000)
        start_time = end_time - (minutes * 60 * 1000)

        request = {
            "logGroupName": log_group_name,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit
        }

        if filter_pattern:
            request["filterPattern"] = filter_pattern

        response = logs_client.filter_log_events(**request)

        events = []

        for event in response.get("events", []):
            message = event.get("message", "")

            # Prevent very large individual log messages from
            # consuming excessive model context.
            if len(message) > 2000:
                message = message[:2000] + "...[truncated]"

            events.append({
                "timestamp": event.get("timestamp"),
                "log_stream_name": event.get("logStreamName"),
                "message": message
            })

        return {
            "success": True,
            "region": REGION,
            "log_group_name": log_group_name,
            "minutes": minutes,
            "filter_pattern": filter_pattern,
            "events": events,
            "count": len(events)
        }

    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "ValidationError",
            "message": "minutes and limit must be valid integers"
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def get_ec2_instance_details(instance_id):
    """
    Get operational details for one specific EC2 instance.

    This tool is read-only and uses the DescribeInstances API.
    """

    if not instance_id:
        return {
            "success": False,
            "error": "ValidationError",
            "message": "instance_id is required"
        }

    try:
        response = ec2_client.describe_instances(
            InstanceIds=[instance_id]
        )

        instances = []

        for reservation in response.get("Reservations", []):
            instances.extend(reservation.get("Instances", []))

        if not instances:
            return {
                "success": False,
                "error": "InstanceNotFound",
                "message": f"No EC2 instance found for instance ID: {instance_id}"
            }

        instance = instances[0]

        tags = {
            tag.get("Key"): tag.get("Value")
            for tag in instance.get("Tags", [])
            if tag.get("Key")
        }

        return {
            "success": True,
            "region": REGION,
            "instance": {
                "instance_id": instance.get("InstanceId"),
                "name": tags.get("Name"),
                "state": instance.get("State", {}).get("Name"),
                "instance_type": instance.get("InstanceType"),
                "availability_zone": (
                    instance.get("Placement", {})
                    .get("AvailabilityZone")
                ),
                "private_ip_address": instance.get("PrivateIpAddress"),
                "public_ip_address": instance.get("PublicIpAddress"),
                "vpc_id": instance.get("VpcId"),
                "subnet_id": instance.get("SubnetId"),
                "security_group_ids": [
                    group.get("GroupId")
                    for group in instance.get("SecurityGroups", [])
                ],
                "iam_instance_profile": (
                    instance.get("IamInstanceProfile", {})
                    .get("Arn")
                ),
                "image_id": instance.get("ImageId"),
                "architecture": instance.get("Architecture"),
                "launch_time": (
                    instance.get("LaunchTime").isoformat()
                    if instance.get("LaunchTime")
                    else None
                ),
                "tags": tags
            }
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
def get_ec2_instance_status(instance_id):
    """
    Get health and status-check information for one specific EC2 instance.

    This tool is read-only and uses the DescribeInstanceStatus API.
    """

    if not instance_id:
        return {
            "success": False,
            "error": "ValidationError",
            "message": "instance_id is required"
        }

    try:
        response = ec2_client.describe_instance_status(
            InstanceIds=[instance_id],
            IncludeAllInstances=True
        )

        statuses = response.get("InstanceStatuses", [])

        if not statuses:
            return {
                "success": False,
                "error": "InstanceStatusNotFound",
                "message": (
                    f"No EC2 instance status information found for "
                    f"instance ID: {instance_id}"
                )
            }

        status = statuses[0]

        system_status = status.get("SystemStatus", {})
        instance_status = status.get("InstanceStatus", {})

        return {
            "success": True,
            "region": REGION,
            "instance_id": status.get("InstanceId"),
            "instance_state": (
                status.get("InstanceState", {}).get("Name")
            ),
            "availability_zone": status.get("AvailabilityZone"),
            "system_status": {
                "status": system_status.get("Status"),
                "details": [
                    {
                        "name": detail.get("Name"),
                        "status": detail.get("Status")
                    }
                    for detail in system_status.get("Details", [])
                ]
            },
            "instance_status": {
                "status": instance_status.get("Status"),
                "details": [
                    {
                        "name": detail.get("Name"),
                        "status": detail.get("Status")
                    }
                    for detail in instance_status.get("Details", [])
                ]
            }
        }

    except ClientError as error:
        return build_error_response(error)

    except Exception as error:
        return {
            "success": False,
            "error": type(error).__name__,
            "message": str(error)
        }
