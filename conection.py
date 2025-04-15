import asyncio
import shutil
import os
from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
load_dotenv()

AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_KEY"]
AZURE_OPENAI_API_VERSION = os.environ["AZURE_OPENAI_VERSION"]
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_MODEL = os.environ["AZURE_OPENAI_DEPLOYMENT_4O_MINI"]


async def run(mcp_server: MCPServer, user_input: str):
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    
    agent = Agent(
        name="MCP Assistant",
        instructions=
        (
            "You are a useful firestore assistant, answer the users queries and do what the user asks of you. Use the provided tools if necessary"
        ),
        model=OpenAIChatCompletionsModel(
            model=AZURE_OPENAI_MODEL,
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

async def main():
    user_input = input("I am an MCP agent that connects to a firestore databse, how can i help you? ")
                
    async with MCPServerStdio(
        cache_tools_list=True,  # Cache the tools list, for demonstration
        params={"command": "python", "args": ["mcpdemo.py"]},
    ) as server:
        with trace(workflow_name="MCP Example"):
            await run(server, user_input)
            await server.cleanup()
            
if __name__ == "__main__":
    
    asyncio.run(main())