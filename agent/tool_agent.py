import os

import boto3
from botocore.exceptions import ClientError

from tools.aws_tools import (
    list_eks_clusters,
    list_ec2_instances,
    list_cloudwatch_alarms,
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
                    "Lists Amazon EKS clusters in the configured AWS "
                    "region. Use this when the user asks about existing "
                    "EKS clusters, current EKS clusters, or how many "
                    "EKS clusters are present."
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

                "Use list_eks_clusters when the user asks which EKS clusters "
                "currently exist or how many EKS clusters are in the AWS region. "

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
            )
        }
    ]


# ============================================================
# Integrated Nova Tool-Use Agent
# ============================================================

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
