"""
This file is the entry point for the Azure Function. It creates an instance of the FastAPI app and wraps it in an Azure Function app. IT SHOULD NOT BE MODIFIED.
"""

import azure.functions as func

from main import app as fastapi_app

# Create an instance of AsgiFunctionApp using the FastAPI app
# The HTTP authorization level is set to anonymous, allowing public access without authorization.
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
