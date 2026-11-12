import os

import boto3
from botocore.exceptions import ClientError

from tools.aws_tools import (
    list_eks_clusters,
    list_ec2_instances,
    list_cloudwatch_alarms,
    get_eks_cluster_details,
    list_eks_nodegroups,
    get_eks_nodegroup_details,
    list_cloudwatch_log_groups,
    get_recent_log_events,
    get_ec2_instance_details,
    get_ec2_instance_status,
)


# ============================================================
# Configuration
# ============================================================

REGION = os.environ.get(
    "AWS_REGION",
    "us-east-1",
)

MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "us.amazon.nova-micro-v1:0",
)


# ============================================================
# Bedrock Client
# ============================================================

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
)


# ============================================================
# Tools Exposed to Nova
# ============================================================

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "list_eks_clusters",
                "description": (
                    "List the Amazon EKS clusters that currently exist in the AWS "
                    "account and configured region. Use this for cluster discovery, "
                    "listing, or counting. Do not use this to retrieve details for "
                    "a specific cluster when its name is already provided."
                ),
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "list_ec2_instances",
                "description": (
                    "Lists Amazon EC2 instances in the configured AWS "
                    "region, including instance ID, name, type, state, "
                    "and IP information."
                ),
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "list_cloudwatch_alarms",
                "description": (
                    "Lists Amazon CloudWatch metric alarms and their "
                    "current states in the configured AWS region."
                ),
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                },
            }
        },
        {
    "toolSpec": {
        "name": "get_eks_cluster_details",
        "description": (
            "Get current details for one specific Amazon EKS cluster. "
            "Use this directly when the user provides a cluster name and asks "
            "about its status, Kubernetes version, endpoint configuration, "
            "VPC networking, security groups, or control-plane logging. "
            "Do not use list_eks_clusters first when the cluster name is "
            "already known."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": (
                            "The exact name of the EKS cluster."
                        )
                    }
                },
                "required": [
                    "cluster_name"
                ]
            }
        }
    }
},

{
    "toolSpec": {
        "name": "list_eks_nodegroups",
        "description": (
            "List or discover Amazon EKS managed node groups for a specific "
            "EKS cluster. Use this tool when the user asks to list, show, "
            "find, count, discover, or identify node groups in a cluster "
            "and does NOT provide a specific node group name. "
            "This tool requires only cluster_name."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": (
                            "The exact name of the EKS cluster."
                        )
                    }
                },
                "required": [
                    "cluster_name"
                ]
            }
        }
    }
},

{
    "toolSpec": {
        "name": "get_eks_nodegroup_details",
        "description": (
            "Get operational details for ONE SPECIFIC Amazon EKS managed "
            "node group. Use this tool ONLY when the user provides both an "
            "EKS cluster name AND a specific node group name and asks about "
            "that node group's status, health, Kubernetes version, AMI type, "
            "capacity type, instance types, or scaling configuration. "
            "Never use this tool when the user is asking to list or discover "
            "node groups and has not provided a node group name."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": (
                            "The exact name of the EKS cluster."
                        )
                    },
                    "nodegroup_name": {
                        "type": "string",
                        "description": (
                            "The exact name of the EKS managed node group."
                        )
                    }
                },
                "required": [
                    "cluster_name",
                    "nodegroup_name"
                ]
            }
        }
    }
},

{
    "toolSpec": {
        "name": "list_cloudwatch_log_groups",
        "description": (
            "List or discover Amazon CloudWatch Logs log groups. "
            "Use this tool when the user asks to list, show, find, "
            "discover, or identify available CloudWatch log groups. "
            "This tool does not retrieve log events."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
},
{
    "toolSpec": {
        "name": "get_recent_log_events",
        "description": (
            "Retrieve recent log events from ONE SPECIFIC CloudWatch "
            "Logs log group. Use this tool when the user provides a "
            "specific log group name and asks to inspect recent logs, "
            "errors, warnings, failures, or application activity. "
            "Do not use this tool merely to discover log groups."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "log_group_name": {
                        "type": "string",
                        "description": (
                            "Exact CloudWatch Logs log group name, for "
                            "example /aws/lambda/cloudops-ai-agent-dev."
                        )
                    },
                    "minutes": {
                        "type": "integer",
                        "description": (
                            "Number of minutes to search backwards. "
                            "Default is 30 and maximum is 1440."
                        )
                    },
                    "filter_pattern": {
                        "type": "string",
                        "description": (
                            "Optional CloudWatch Logs filter pattern, "
                            "for example ERROR."
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of log events to return. "
                            "Default is 50 and maximum is 100."
                        )
                    }
                },
                "required": [
                    "log_group_name"
                ]
            }
        }
    }
},

{
    "toolSpec": {
        "name": "get_ec2_instance_details",
        "description": (
            "Get configuration and operational details for ONE SPECIFIC "
            "Amazon EC2 instance. Use this tool when the user provides "
            "an EC2 instance ID and asks about its state, instance type, "
            "Availability Zone, IP addresses, VPC, subnet, security groups, "
            "AMI, architecture, IAM instance profile, or tags. "
            "Do not use this tool merely to list or discover EC2 instances."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": (
                            "The specific EC2 instance ID, for example "
                            "i-0123456789abcdef0."
                        )
                    }
                },
                "required": [
                    "instance_id"
                ]
            }
        }
    }
},

{
    "toolSpec": {
        "name": "get_ec2_instance_status",
        "description": (
            "Get health and status-check information for ONE SPECIFIC "
            "Amazon EC2 instance. Use this tool when the user provides "
            "an EC2 instance ID and asks whether the instance is healthy, "
            "reachable, impaired, or whether its EC2 system or instance "
            "status checks are passing. "
            "Do not use this tool for general EC2 configuration details."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": (
                            "The specific EC2 instance ID whose health "
                            "status should be checked."
                        )
                    }
                },
                "required": [
                    "instance_id"
                ]
            }
        }
    }
},
    ]
}


# ============================================================
# Tool Allowlist / Dispatcher
# ============================================================

def execute_tool(tool_name, tool_input):
    """
    Execute only explicitly approved AWS tools.

    Nova never receives unrestricted boto3 access.
    """

    print(
        "Requested tool:",
        tool_name,
    )

    print(
        "Tool input:",
        tool_input,
    )

    if tool_name == "list_eks_clusters":
        return list_eks_clusters()

    if tool_name == "list_ec2_instances":
        return list_ec2_instances()

    if tool_name == "list_cloudwatch_alarms":
        return list_cloudwatch_alarms()

    if tool_name == "get_eks_cluster_details":
        return get_eks_cluster_details(
            tool_input.get("cluster_name")
    )

    if tool_name == "list_eks_nodegroups":
        return list_eks_nodegroups(
           tool_input.get("cluster_name")
    )

    if tool_name == "get_eks_nodegroup_details":
        return get_eks_nodegroup_details(
           tool_input.get("cluster_name"),
           tool_input.get("nodegroup_name")
    )

    if tool_name == "list_cloudwatch_log_groups":
        return list_cloudwatch_log_groups()

    if tool_name == "get_recent_log_events":
        return get_recent_log_events(
            log_group_name=tool_input.get("log_group_name"),
            minutes=tool_input.get("minutes", 30),
            filter_pattern=tool_input.get("filter_pattern"),
            limit=tool_input.get("limit", 50)
    )

    if tool_name == "get_ec2_instance_details":
        return get_ec2_instance_details(
           instance_id=tool_input.get("instance_id")
    )

    if tool_name == "get_ec2_instance_status":
        return get_ec2_instance_status(
           instance_id=tool_input.get("instance_id")
    )

    return {
        "success": False,
        "error_code": "ToolNotAllowed",
        "error_message": (
            f"Tool '{tool_name}' is not approved."
        ),
    }


# ============================================================
# Extract Text
# ============================================================

def extract_text(message):
    """
    Extract text blocks from a Bedrock Converse API message.
    """

    text_parts = []

    for block in message.get(
        "content",
        [],
    ):
        if "text" in block:
            text_parts.append(
                block["text"]
            )

    return "\n".join(text_parts)


# ============================================================
# System Prompt
# ============================================================

def build_system_prompt():
    """
    Instructions that distinguish live AWS account state
    from Knowledge Base / runbook information.
    """

    return [
        {
            "text": (
                "You are a CloudOps AI assistant with access to both "
                "CloudOps knowledge-base context and approved live AWS tools. "

                "IMPORTANT TOOL-USAGE RULES: "

                "When the user asks about the CURRENT or LIVE state of their "
                "AWS environment, account, resources, clusters, instances, "
                "or alarms, you MUST use the appropriate available AWS tool "
                "instead of answering from the knowledge-base context. "

                "Use list_eks_clusters ONLY when the user asks to discover, list, "
                "count, or identify which EKS clusters currently exist. "

                "Use list_ec2_instances when the user asks which EC2 instances "
                "currently exist, their state, or their basic instance details. "

                "Use list_cloudwatch_alarms when the user asks about current "
                "CloudWatch alarms or alarm states. "

                "Knowledge-base context contains documentation and runbooks. "
                "It must not be treated as evidence of the current state of "
                "the AWS account. "

                "For documentation, runbook, explanation, or procedure questions, "
                "use the provided knowledge context and do not call an AWS tool "
                "unless live AWS state is also required. "

                "Never claim that live AWS state is unavailable from the "
                "knowledge base when an appropriate live AWS tool is available."

                "Use get_eks_cluster_details when the user provides a specific EKS "
                "cluster name and asks about that cluster's current status, Kubernetes "
                "version, endpoint configuration, VPC networking, security groups, "
                "or control-plane logging. "

                "When a specific EKS cluster name is already provided, do NOT call "
                "list_eks_clusters first to check whether it exists. Call "
                "get_eks_cluster_details directly. "

                "Follow these EKS node-group tool routing rules strictly: "

                "If the user asks to list, show, find, count, discover, or identify "
                "the node groups in a specific EKS cluster, and no specific node "
                "group name is provided, use list_eks_nodegroups. "

                "Use get_eks_nodegroup_details ONLY when BOTH the cluster name and "
                "a specific node group name are explicitly provided by the user. "

                "Never call get_eks_nodegroup_details without a nodegroup_name. "

                "When both cluster_name and nodegroup_name are already known, call "
                "get_eks_nodegroup_details directly and do not call "
                "list_eks_nodegroups first. "

                "Follow these EC2 tool routing rules strictly: "

                "If the user asks to list, show, find, count, discover, or identify EC2 "
                "instances and does not provide a specific instance ID to inspect, use "
                "list_ec2_instances. "

                "If the user provides a specific EC2 instance ID and asks about its state, "
                "instance type, networking, VPC, subnet, security groups, AMI, architecture, "
                "IAM instance profile, tags, or other configuration details, use "
                "get_ec2_instance_details. "

                "If the user provides a specific EC2 instance ID and asks whether it is "
                "healthy, reachable, impaired, or whether its system or instance status "
                "checks are passing, use get_ec2_instance_status. "

                "Never call get_ec2_instance_details or get_ec2_instance_status without "
                "an instance_id. "

                "When a specific instance_id is already known, call the appropriate "
                "specific EC2 tool directly and do not call list_ec2_instances first. "

                "Follow these CloudWatch Logs tool routing rules strictly: "
                "If the user asks to list, show, find, discover, or identify available "
                "CloudWatch log groups and does not provide a specific log group to inspect, "
                "use list_cloudwatch_log_groups. "
                "If the user provides a specific CloudWatch log group name and asks to inspect "
                "recent logs, errors, warnings, failures, or activity, use "
                "get_recent_log_events. "
                "Do not use get_recent_log_events without a log_group_name. "
                "When the exact log_group_name is already known, call "
                "get_recent_log_events directly and do not call "
                "list_cloudwatch_log_groups first. "

                "Return only the final user-facing answer. "
                "Do not include internal reasoning, chain-of-thought, analysis, "
                "scratch work, or <thinking> tags in the response. "
            )
        }
    ]


# ============================================================
# Integrated Nova Tool-Use Agent# ============================================================

def run_agent_with_messages(messages):
    """
    Run the Nova tool-use loop using an already constructed
    Converse API message history.

    The main CloudOps application can provide:
      - DynamoDB conversation history
      - Knowledge Base / RAG context
      - Current user request

    Nova can additionally request one of the approved AWS tools.
    """

    try:
        print(
            "Invoking Nova with tool support"
        )

        system_prompt = build_system_prompt()

        # ----------------------------------------------------
        # First Nova invocation
        # ----------------------------------------------------

        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_prompt,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0,
            },
        )

        assistant_message = response[
            "output"
        ][
            "message"
        ]

        stop_reason = response.get(
            "stopReason"
        )

        print(
            "Nova stop reason:",
            stop_reason,
        )

        # ----------------------------------------------------
        # Nova answered without requiring a live AWS tool
        # ----------------------------------------------------

        if stop_reason != "tool_use":
            return {
                "success": True,
                "answer": extract_text(
                    assistant_message
                ),
                "tool_used": None,
                "tool_result": None,
            }

        # ----------------------------------------------------
        # Nova requested a tool
        # ----------------------------------------------------

        messages.append(
            assistant_message
        )

        tool_request = None

        for block in assistant_message.get(
            "content",
            [],
        ):
            if "toolUse" in block:
                tool_request = block[
                    "toolUse"
                ]
                break

        if tool_request is None:
            return {
                "success": False,
                "error": (
                    "Nova returned tool_use but no "
                    "toolUse request was found."
                ),
            }

        tool_use_id = tool_request[
            "toolUseId"
        ]

        tool_name = tool_request[
            "name"
        ]

        tool_input = tool_request.get(
            "input",
            {},
        )

        print(
            "Nova requested tool:",
            tool_name,
        )

        # ----------------------------------------------------
        # Execute only an allowlisted AWS tool
        # ----------------------------------------------------

        tool_result = execute_tool(
            tool_name,
            tool_input,
        )

        print(
            "AWS tool result:",
            tool_result,
        )

        tool_status = (
            "success"
            if tool_result.get("success")
            else "error"
        )

        # ----------------------------------------------------
        # Return the tool result to Nova
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [
                                {
                                    "json": tool_result
                                }
                            ],
                            "status": tool_status,
                        }
                    }
                ],
            }
        )

        print(
            "Returning AWS tool result to Nova"
        )

        # ----------------------------------------------------
        # Second Nova invocation
        # ----------------------------------------------------

        final_response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_prompt,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0,
            },
        )

        final_message = final_response[
            "output"
        ][
            "message"
        ]

        return {
            "success": True,
            "answer": extract_text(
                final_message
            ),
            "tool_used": tool_name,
            "tool_result": tool_result,
        }

    except ClientError as error:
        error_code = error.response[
            "Error"
        ].get(
            "Code",
            "UnknownAWSClientError",
        )

        print(
            "Agent Bedrock ClientError:",
            error_code,
        )

        return {
            "success": False,
            "error": "Bedrock agent request failed",
            "error_code": error_code,
        }

    except Exception as error:
        print(
            "Agent unexpected error:",
            type(error).__name__,
            str(error),
        )

        return {
            "success": False,
            "error": "Agent execution failed",
            "error_type": type(
                error
            ).__name__,
        }


# ============================================================
# Standalone Nova Tool-Use Agent
# ============================================================

def run_agent(user_message):
    """
    Standalone agent used by the temporary tool-test Lambda.

    Nova can either:
      1. Answer directly.
      2. Request one of the approved AWS tools.
    """

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": user_message
                }
            ],
        }
    ]

    try:
        print(
            "Sending request to Nova Micro"
        )

        system_prompt = build_system_prompt()

        # ----------------------------------------------------
        # First Nova invocation
        # ----------------------------------------------------

        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_prompt,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0,
            },
        )

        assistant_message = response[
            "output"
        ][
            "message"
        ]

        stop_reason = response.get(
            "stopReason"
        )

        print(
            "Nova stop reason:",
            stop_reason,
        )

        # ----------------------------------------------------
        # No tool required
        # ----------------------------------------------------

        if stop_reason != "tool_use":
            return {
                "success": True,
                "answer": extract_text(
                    assistant_message
                ),
                "tool_used": None,
                "tool_result": None,
            }

        # ----------------------------------------------------
        # Tool requested
        # ----------------------------------------------------

        messages.append(
            assistant_message
        )

        tool_request = None

        for block in assistant_message.get(
            "content",
            [],
        ):
            if "toolUse" in block:
                tool_request = block[
                    "toolUse"
                ]
                break

        if tool_request is None:
            return {
                "success": False,
                "error": (
                    "Nova returned tool_use but no "
                    "toolUse request was found."
                ),
            }

        tool_use_id = tool_request[
            "toolUseId"
        ]

        tool_name = tool_request[
            "name"
        ]

        tool_input = tool_request.get(
            "input",
            {},
        )

        # ----------------------------------------------------
        # Execute through our allowlist
        # ----------------------------------------------------

        tool_result = execute_tool(
            tool_name,
            tool_input,
        )

        print(
            "Tool execution result:",
            tool_result,
        )

        tool_status = (
            "success"
            if tool_result.get("success")
            else "error"
        )

        # ----------------------------------------------------
        # Send tool result back to Nova
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [
                                {
                                    "json": tool_result
                                }
                            ],
                            "status": tool_status,
                        }
                    }
                ],
            }
        )

        print(
            "Returning tool result to Nova"
        )

        # ----------------------------------------------------
        # Second Nova invocation
        # ----------------------------------------------------

        final_response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_prompt,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={
                "maxTokens": 1000,
                "temperature": 0,
            },
        )

        final_message = final_response[
            "output"
        ][
            "message"
        ]

        return {
            "success": True,
            "answer": extract_text(
                final_message
            ),
            "tool_used": tool_name,
            "tool_result": tool_result,
        }

    except ClientError as error:
        error_code = error.response[
            "Error"
        ].get(
            "Code",
            "UnknownAWSClientError",
        )

        print(
            "Bedrock ClientError:",
            error_code,
        )

        return {
            "success": False,
            "error": "Bedrock request failed",
            "error_code": error_code,
        }

    except Exception as error:
        print(
            "Agent unexpected error:",
            type(error).__name__,
            str(error),
        )

        return {
            "success": False,
            "error": "Agent execution failed",
            "error_type": type(
                error
            ).__name__,
        }
