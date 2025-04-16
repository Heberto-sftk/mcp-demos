from fastapi import FastAPI

import functions

app = FastAPI(
    title="MCP Agent API",
    description="API for accesing an assistant agent for MCPs.",
    version="0.1.0",
)

app.include_router(functions.router, prefix="/prompts", tags=["Prompts"])


@app.get("/")
async def read_root():
    """
    Endpoint for testing purposes.

    Returns:
        dict: A dictionary with a success message.
    """
    return {"success": True, "message": "This endpoint is for testing purposes only."}