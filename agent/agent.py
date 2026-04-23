import sys
import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import search_google_web, generate_implementation_plan, estimate_budget, export_pdf_and_json
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse

# -- LISTAS DE FILTROS PARA CALLBACKS --
PALABRAS_MALSONANTES = ["tonto", "idiota", "imbécil", "estúpido", "mierda"]
PALABRAS_RACISTAS = ["negrata", "gitanaco", "panchito", "sudaca", "moro"]

def _censurar_texto(texto: str, lista_prohibidas: list) -> str:
    for palabra in lista_prohibidas:
        patron = r"\b" + re.escape(palabra) + r"\b"
        texto = re.sub(patron, "[censurado]", texto, flags=re.IGNORECASE)
    return texto

def callback_malsonantes(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Primer Callback de intercepción. Limpia malas palabras del input de usuario."""
    if not llm_request.contents:
        return None
    for content in llm_request.contents:
        if getattr(content, "role", None) != "user":
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            if hasattr(part, "text") and part.text:
                part.text = _censurar_texto(part.text, PALABRAS_MALSONANTES)
    return None

def callback_racistas(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Segundo Callback de intercepción encadenado. Limpia connotaciones racistas."""
    if not llm_request.contents:
        return None
    for content in llm_request.contents:
        if getattr(content, "role", None) != "user":
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            if hasattr(part, "text") and part.text:
                part.text = _censurar_texto(part.text, PALABRAS_RACISTAS)
    return None

def eliminar_pensamientos_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """Callback post-modelo: elimina las parts con thought=true para que la UI solo muestre el mensaje al usuario."""
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return None

    parts_limpios = [
        part for part in llm_response.content.parts
        if not getattr(part, 'thought', False)
    ]

    # Si tras filtrar no queda nada, no alteramos la respuesta
    if not parts_limpios:
        return None

    llm_response.content.parts = parts_limpios
    return llm_response

root_agent = LlmAgent(
    name="smartcity_generative_agent",
    model=LiteLlm(
        model="openai/gpt-oss-120b",
        api_base=os.environ.get("OPENAI_API_BASE", "https://api.ejemplo.es/"),
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    ),
    description="Agente analista de Smart Cities avanzado con interceptores de input.",
    before_model_callback=[callback_malsonantes, callback_racistas],
    after_model_callback=eliminar_pensamientos_callback,
    instruction=(
        "Actuarás en dos fases claramente diferenciadas.\n\n"
        "### FASE 1: Conversacional e Ideación\n"
        "Si el usuario pide EXPLÍCITAMENTE generar un informe o plan sobre un tema concreto de entrada (ej. 'Genera un informe sobre IA en Educación'), SALTA DIRECTAMENTE A LA FASE 2. No intentes forzar la charla de Smart Cities si el prompt es una orden directa de generación.\n"
        "En caso contrario, si el usuario solo te saluda o pregunta dudas generales, tu misión es dialogar con él. Actúa como Asesor de Ciudades Inteligentes. Sugiere funciones (IoT, semáforos, sensores, etc.) y explica casos de uso.\n"
        "Espera a que el usuario confirme qué funciones quiere. NO EJECUTES TOOLS HASTA QUE HAYA UN TEMA O FUNCIONES CLARAS.\n\n"
        "### FASE 2: Recopilación y Redacción Autónoma\n"
        "UNA VEZ que el usuario indique claramente las funciones o el tema del informe, "
        "ejecuta AUTOMÁTICA Y CONSECUTIVAMENTE tus tools en este ORDEN EXACTO:\n"
        "¡ATENCIÓN! Sé MUY BREVE razonando entre herramientas. Escribe máximo UNA SOLA FRASE antes de invocar cada tool.\n\n"
        "1. Llama a 'search_google_web' para investigar los conceptos técnicos clave del proyecto. "
        "Puedes hacer MÁXIMO 3 búsquedas en total (la herramienta bloqueará más). Usa búsquedas variadas para obtener URLs de referencia reales.\n"
        "2. Con la información investigada, llama a 'generate_implementation_plan' pasándole la lista de funciones en 'funciones' y, MUY IMPORTANTE, "
        "redactando TÚ MISMO un plan de implementación técnico exhaustivo y detallado (mínimo 150 palabras) en 'plan_detallado'. "
        "Usa la información real que obtuviste de las búsquedas. Incluye fases de despliegue específicas para cada función.\n"
        "3. Llama a 'estimate_budget' pasándole el plan resultante del paso 2 en 'implementation_plan' y, MUY IMPORTANTE, "
        "redactando TÚ MISMO un presupuesto detallado y profesional (mínimo 150 palabras) en 'presupuesto_detallado' "
        "desglosando costes de hardware, software y mantenimiento. La herramienta calculará cifras numéricas automáticas que complementarán tu análisis.\n"
        "4. Finalmente llama a 'export_pdf_and_json', proporcionando: tu propio título atractivo, "
        "redactando TÚ MISMO un report_summary extenso como Introducción (mínimo 150 palabras), "
        "pasándole el implementation_plan del paso 2, el budget del paso 3, "
        "redactando TÚ MISMO unas conclusions detalladas y reflexivas (mínimo 150 palabras), "
        "tus referencias (URLs reales de tus búsquedas del paso 1) y usando pdf_path='output/informe_smartcity_final.pdf'.\n"
        "5. AL VOLVER DE export_pdf_and_json, responde al usuario con un mensaje breve, amable y en lenguaje natural. "
        "NO muestres el JSON crudo ni datos técnicos internos. Solo un mensaje humano confirmando que el informe está listo."
    ),
    tools=[search_google_web, generate_implementation_plan, estimate_budget, export_pdf_and_json]
)

