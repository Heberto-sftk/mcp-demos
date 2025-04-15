# MCP Demo: OpenAI + Firestore

# Importaciones base
import json
from typing import Optional
from datetime import datetime

# Importaciones para MCP
from mcp.server.fastmcp import FastMCP, Context

# librería para Azure OpenAI
from openai import AzureOpenAI

#Importaciones para Firebase
import firebase_admin
from firebase_admin import credentials, firestore

import os

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


# Creación del servidor MCP
mcp = FastMCP(
    name = "OpenAIFirestoreDemo",
    description = "Demo de integración entre OpenAI y Firestore",
    host = "127.0.0.1",
    port = 5000,
    timeout = 30000
)


# Inicializar el cliente
CLIENT = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"], 
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version= os.environ["AZURE_OPENAI_VERSION"]
)


# Inicializar credenciales de Firebase
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)

# Inicializar Firestore
db = firestore.client()




# funcion para generar respuestas con Azure OpenAI
def generate_response(prompt: str, content: str) -> str:
    """Genera una respuesta utilizando Azure OpenAI"""
    # Aquí puedes personalizar el prompt según tus necesidades
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    
    response = CLIENT.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_4O_MINI"],
        messages=messages
    )
    
    return response.choices[0].message.content

#Implementacion de recursos de mcp
@mcp.resource("notes://{user_id}/all")
def get_user_notes(user_id: str) -> Optional[list]:
    """Obtiene todas las notas de un usuario específico"""
    notes_ref = db.collection("tests").where("user_id", "==", user_id)
    notes = notes_ref.stream()
    
    # Convertir a lista de diccionarios
    notes_list = [note.to_dict() for note in notes]
    
    return notes_list

@mcp.resource("notes://{note_id}")
def get_note(note_id: str) -> Optional[dict]:
    """Obtiene una nota específica por su ID"""
    note_ref = db.collection("tests").document(note_id)
    note = note_ref.get()
    
    if note.exists:
        return note.to_dict()
    else:
        return None


@mcp.resource("config://app")
def get_app_config() -> str:
    """Proporciona la configuración de la aplicación"""
    config = {
        "name": "OpenAI-Firestore Notes App",
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat()
    }
    return json.dumps(config, indent=2)

#Implementacion de tools de mcp (funcionan como posts de la API)

@mcp.tool()
async def analyze_sentiment(text: str) -> str:
    """Analiza el sentimiento de un texto usando OpenAI"""
    prompt = "Analize the sentiment of the following text and return a JSON object with the sentiment and confidence score."
    # Generar respuesta utilizando el modelo de OpenAI
    result = generate_response(prompt, text)

    
    # Intentamos parsear la respuesta como JSON
    try:
        return result
    except:
        # Si no podemos parsear la respuesta, devolvemos un formato estándar
        return json.dumps({
            "sentiment": "neutral",
            "confidence": 0.5,
            "raw_response": result
        })

@mcp.tool(
    name="create_note",
    description="Crea una nueva nota para un usuario específico",
)
async def create_note(user_id: str, title: str, content: str) -> str:
    """Crea una nueva nota para un usuario específico"""
    # Crear un nuevo documento en Firestore
    notes_ref = db.collection("tests").add({
        "user_id": user_id,
        "title": title,
        "content": content,
        "created_at": datetime.now()
    })
    
    
    return f"Nota creada "

@mcp.tool()
async def update_note(note_id: str, title: str, content: str) -> str:
    """Actualiza una nota existente"""
    # Obtener la referencia del documento
    note_ref = db.collection("tests").document(note_id)
    
    # Actualizar el documento
    note_ref.update({
        "title": title,
        "content": content,
        "updated_at": datetime.now()
    })
    
    return f"Nota actualizada"

@mcp.tool()
async def delete_note(note_id: str) -> str:
    """Elimina una nota existente"""
    # Obtener la referencia del documento
    note_ref = db.collection("tests").document(note_id)
    
    # Eliminar el documento
    note_ref.delete()
    
    return f"Nota eliminada"

# Implementación de Prompts
# Los prompts son plantillas reutilizables para interacciones con el LLM

@mcp.prompt()
def note_creation_template(user_id: str, titulo: str, contenido: str) -> str:
    """Plantilla para la creación de una nueva nota"""
    return f"""
Por favor crea una nueva nota para el usuario {user_id}.
Necesito un título {titulo} y contenido para la nota {contenido}.
Puedes usar la herramienta create_note para añadirla a la base de datos.
"""

@mcp.prompt()
def analyze_notes_template(user_id: str) -> str:
    """Plantilla para analizar las notas de un usuario"""
    return f"""
Por favor analiza las notas del usuario {user_id}.
Primero, obtén todas las notas usando el recurso notes://{user_id}/all
Luego, proporciona un resumen de las principales ideas y temas encontrados.
Si es apropiado, sugiere formas de organizar mejor la información.
"""

@mcp.prompt()
def improve_note_content(note_id: str) -> str:
    """Plantilla para mejorar el contenido de una nota"""
    return f"""
Por favor ayúdame a mejorar el contenido de la nota con ID {note_id}.
Primero, obtén los detalles de la nota usando el recurso notes://{note_id}
Luego, sugiere cómo podría mejorar la claridad, estructura y contenido.
Finalmente, ofrece una versión mejorada que pueda usar para actualizar la nota.
"""
    
if __name__ == "__main__":
    mcp.run(transport="stdio")