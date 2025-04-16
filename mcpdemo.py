# MCP Demo: OpenAI + Firestore

# Importaciones base
import json
from typing import Optional
from datetime import datetime

# Importaciones para MCP
from mcp.server.fastmcp import FastMCP, Context
from agents.mcp import MCPServer, MCPServerSse, MCPServerSseParams

# Librería para Azure OpenAI
from openai import AsyncAzureOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, trace

# Importaciones para Firebase
import firebase_admin
from firebase_admin import credentials, firestore

import os
from dotenv import load_dotenv
import uvicorn

# Cargar variables de entorno
load_dotenv()

# Creación del servidor MCP
mcp = FastMCP(
    name="OpenAIFirestoreDemo",
    description="Demo de integración entre OpenAI y Firestore",
    host="127.0.0.1",
    port=5000,
    timeout=30000
)

# Inicializar el cliente de Azure OpenAI
CLIENT = AsyncAzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["AZURE_OPENAI_VERSION"]
)

# Inicializar credenciales de Firebase
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)

# Inicializar Firestore
db = firestore.client()

# Función para generar respuestas con Azure OpenAI
async def generate_response(prompt: str, contenido: str) -> str:
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": contenido}
    ]

    response = await CLIENT.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_4O_MINI"],
        messages=messages
    )

    return response.choices[0].message.content




# Recursos MCP
@mcp.resource("notes://{user_id}/all")
def get_user_notes(user_id: str) -> Optional[list]:
    notes_ref = db.collection("tests").where("user_id", "==", user_id)
    notes = notes_ref.stream()
    return [note.to_dict() for note in notes]

@mcp.resource("notes://{note_id}")
def get_note(note_id: str) -> Optional[dict]:
    note_ref = db.collection("tests").document(note_id)
    note = note_ref.get()
    return note.to_dict() if note.exists else None

@mcp.resource("config://app")
def get_app_config() -> str:
    config = {
        "name": "OpenAI-Firestore Notes App",
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat()
    }
    return json.dumps(config, indent=2)

# Herramientas MCP
@mcp.tool()
async def analyze_sentiment(text: str) -> str:
    prompt = (
        "Analiza el sentimiento del siguiente texto y devuelve un objeto JSON con los campos 'sentiment' y 'confidence'."
    )
    try:
        result = await generate_response(prompt, text)
        return result
    except Exception as e:
        return f"Error al analizar el sentimiento: {str(e)}"


@mcp.tool(name="create_note", description="Crea una nueva nota para un usuario específico")
async def create_note(user_id: str, title: str, contenido: str) -> str:
    try:
        db.collection("tests").add({
            "user_id": user_id,
            "title": title,
            "content": contenido,
            "created_at": datetime.now()
        })
        return f"Nota creada exitosamente para el usuario {user_id}"
    except Exception as e:
        return f"Error al crear la nota: {str(e)}"



@mcp.tool()
async def update_note(note_id: str, title: str, contenido: str) -> str:
    try:
        note_ref = db.collection("tests").document(note_id)
        note_ref.update({
            "title": title,
            "content": contenido,
            "updated_at": datetime.now()
        })
        return f"Nota {note_id} actualizada correctamente"
    except Exception as e:
        return f"Error al actualizar la nota {note_id}: {str(e)}"


@mcp.tool()
async def delete_note(note_id: str) -> str:
    try:
        note_ref = db.collection("tests").document(note_id)
        note_ref.delete()
        return f"Nota {note_id} eliminada correctamente"
    except Exception as e:
        return f"Error al eliminar la nota {note_id}: {str(e)}"



# Prompts MCP
@mcp.prompt()
def note_creation_template(user_id: str, titulo: str, contenido: str) -> str:
    return f"""
Por favor crea una nueva nota para el usuario {user_id}.
Necesito un título {titulo} y contenido para la nota {contenido}.
Puedes usar la herramienta create_note para añadirla a la base de datos.
"""

@mcp.prompt()
def analyze_notes_template(user_id: str) -> str:
    return f"""
Por favor analiza las notas del usuario {user_id}.
Primero, obtén todas las notas usando el recurso notes://{user_id}/all
Luego, proporciona un resumen de las principales ideas y temas encontrados.
Si es apropiado, sugiere formas de organizar mejor la información.
"""

@mcp.prompt()
def improve_note_content(note_id: str) -> str:
    return f"""
Por favor ayúdame a mejorar el contenido de la nota con ID {note_id}.
Primero, obtén los detalles de la nota usando el recurso notes://{note_id}
Luego, sugiere cómo podría mejorar la claridad, estructura y contenido.
Finalmente, ofrece una versión mejorada que pueda usar para actualizar la nota.
"""


# Ejecutar el servidor
if __name__ == "__main__":
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=3000)