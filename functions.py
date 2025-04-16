import logging
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException
from openai import AsyncAzureOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.mcp import MCPServerSseParams
import os

router = APIRouter()


async def run(mcp_servers: list[MCPServer], user_input: str):
    client = AsyncAzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version=os.environ["AZURE_OPENAI_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    )
    
    agent = Agent(
        name="MCP Assistant",
        instructions=(
            "You are a capable MCP assistant with access to multiple tool-enabled MCP servers."  
            "Your role is to understand user requests, reason through available options, and use tools, prompts, or resources as needed to fulfill the user's intent."
            "Fulfill all of the users requests to the best of your ability."  
            "If the request can be best addressed through a tool or external resource, use it. " 
            "If not, provide a direct and helpful answer based on your own capabilities."  
            "Always strive to be efficient, precise, and helpful."  
        ),
        model=OpenAIChatCompletionsModel(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT_4O_MINI"],
            openai_client=client,
        ),
        mcp_servers=mcp_servers,
    )
    
    print("\n" + "-" * 40)
    print(f"Running: {user_input}")
    result = await Runner.run(starting_agent=agent, input=user_input)
    print("-" * 40 + "\n")
    print("Result:")
    final_output = result.final_output
    print(final_output)
    return str(final_output)

@router.post("/mcp-agent", description="Send user input to an agent that uses multiple MCP servers.")
async def mcp_agent(
    user_input: str,
    mcp_links: list[str]  # acepta una lista de URLs
):
    """
    Endpoint to send user input to an agent that uses multiple MCP servers.
    Args:
        user_input (str): The user input to be processed by the agent.
        mcp_links (List[str]): A list of MCP server URLs.
    Returns:
        str: The response from the agent.
    """
    servers = []

    try:
        # Abrimos todas las conexiones SSE a los servidores MCP
        for link in mcp_links:
            server = MCPServerSse(MCPServerSseParams(url=link))
            await server.__aenter__()
            servers.append(server)

        with trace(workflow_name="MCP Multiple Servers Example"):
            result = await run(servers, user_input)

        # Cleanup de todos los servidores
        for server in servers:
            await server.cleanup()
            await server.__aexit__(None, None, None)

        return result

    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
