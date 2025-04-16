import logging
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException
from openai import AsyncAzureOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.mcp import MCPServerSseParams
import os

router = APIRouter()


async def run(mcp_server: MCPServer, user_input: str):
    client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.environ["AZURE_OPENAI_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )
    
    agent = Agent(
        name="MCP Assistant",
        instructions=
        (
            "You are a useful firestore assistant, answer the users queries and do what the user asks of you. Use the provided tools if necessary"
        ),
        model=OpenAIChatCompletionsModel(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT_4O_MINI"],
            openai_client=client,
        ),
        mcp_servers=[mcp_server],
    )
    
    print("\n" + "-" * 40)
    print(f"Running: {user_input}")
    result = await Runner.run(starting_agent=agent, input=user_input)
    print("-" * 40 + "\n")
    print("Result:")
    final_output = result.final_output
    print(final_output)
    return str(final_output)

@router.post("/mcp-agent", description="Send user input to an agent that uses a specific MCP server.")
async def mcp_agent(
    user_input: str,
    mcp_link: str
) :
    """
    Endpoint to send user input to an agent that uses a specific MCP server.
    Args:
        user_input (str): The user input to be processed by the agent.
        mcp_link (str): The link to the MCP server.
    Returns:
        str: The response from the agent.
    """
    try:
        async with MCPServerSse(
            MCPServerSseParams(url=mcp_link)
        ) as server:
            with trace(workflow_name="MCP Example"):
                result = await run(server, user_input)
                await server.cleanup()
        return result
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")