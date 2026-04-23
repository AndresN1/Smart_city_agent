# 🏙️ Smart City Agent — Asesor Inteligente con Google ADK

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Google ADK](https://img.shields.io/badge/Framework-Google_ADK-orange.svg)
![LLM](https://img.shields.io/badge/LLM-gpt--oss--120b-green.svg)
![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)

Agente conversacional construido con el **Google Agent Development Kit (ADK)** que actúa como asesor experto en **Ciudades Inteligentes (Smart Cities)**. A través de un diálogo natural, el agente ayuda al usuario a idear funciones inteligentes para su ciudad y genera automáticamente un informe técnico completo en formato PDF con plan de implementación y presupuesto.

---

## Índice

- [Descripción General](#descripción-general)
- [Arquitectura del Agente](#arquitectura-del-agente)
- [Herramientas (Tools)](#herramientas-tools)
- [Sistema de Callbacks](#sistema-de-callbacks)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Ejemplo de Interacción](#ejemplo-de-interacción)
- [Salida Generada](#salida-generada)
- [Evaluación Automática](#evaluación-automática)
- [Autores](#autores)

---

## Descripción General

Este proyecto implementa un agente LLM de **dos fases** que combina conversación libre con ejecución autónoma de herramientas:

1. **Fase de Ideación** — El agente dialoga con el usuario como asesor experto, sugiriendo funcionalidades inteligentes (IoT, semáforos inteligentes, sensores ambientales, videovigilancia con IA, etc.) y negociando cuáles implementar.

2. **Fase de Ejecución Autónoma** — Una vez el usuario confirma las funciones elegidas, el agente encadena automáticamente 4 herramientas para generar un informe técnico completo en PDF.

---

## Arquitectura del Agente

```
┌─────────────────────────────────────────────────────┐
│                   Usuario (Chat)                     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│          CALLBACKS PRE-MODELO (before_model)         │
│  ┌────────────────────┐  ┌────────────────────────┐  │
│  │ callback_malsonantes│  │  callback_racistas     │  │
│  │ Filtra insultos     │  │  Filtra racismo        │  │
│  └────────────────────┘  └────────────────────────┘  │
└──────────────────────┬───────────────────────────────┘
                       │ (input sanitizado)
                       ▼
┌──────────────────────────────────────────────────────┐
│              LLM (gpt-oss-120b vía LiteLLM)          │
│                                                      │
│  Fase 1: Conversación libre (sin tools)              │
│  Fase 2: Encadenamiento autónomo de tools            │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│         CALLBACK POST-MODELO (after_model)           │
│  ┌──────────────────────────────────────────────┐    │
│  │ eliminar_pensamientos_callback                │    │
│  │ Filtra "thought: true" → UI limpia            │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────┬───────────────────────────────┘
                       │ (solo mensaje al usuario)
                       ▼
┌──────────────────────────────────────────────────────┐
│                   Usuario (Chat)                     │
└──────────────────────────────────────────────────────┘
```

---

## Herramientas (Tools)

El agente dispone de 4 herramientas que ejecuta secuencialmente durante la Fase 2:

| # | Herramienta | Descripción |
|---|-------------|-------------|
| 1 | `generate_implementation_plan` | Recibe la lista de funciones inteligentes elegidas y genera un plan de implementación técnico detallado con fases de despliegue por cada función. |
| 2 | `estimate_budget` | Analiza el plan de implementación y calcula un presupuesto desglosado realista (hardware, software, mantenimiento) mediante heurísticas internas. |
| 3 | `search_google_web` | Busca en Internet (vía DuckDuckGo) información técnica real sobre los conceptos clave del proyecto para obtener URLs de referencia bibliográfica. |
| 4 | `export_pdf_and_json` | Consolida toda la información (introducción, plan, presupuesto, conclusiones, referencias) en un documento PDF profesional y devuelve metadatos JSON estructurados. |

### Flujo de ejecución de herramientas

```
generate_implementation_plan → estimate_budget → search_google_web → export_pdf_and_json
        (funciones)              (plan texto)        (conceptos)         (todo consolidado)
              │                       │                    │                      │
              └───────────────────────┴────────────────────┴──────────────────────┘
                                                                          ▼
                                                                   📄 PDF Final
                                                          output/informe_smartcity_final.pdf
```

---

## Sistema de Callbacks

El agente implementa **3 callbacks** que interceptan el flujo de datos antes y después del modelo LLM:

### Before Model (Pre-procesamiento del input)

1. **`callback_malsonantes`** — Intercepta el texto del usuario antes de enviarlo al LLM. Detecta mediante expresiones regulares palabras malsonantes (`tonto`, `idiota`, `imbécil`, `estúpido`, `mierda`) y las reemplaza por `[censurado]`.

2. **`callback_racistas`** — Segundo filtro encadenado que detecta terminología racista (`negrata`, `sudaca`, `moro`, etc.) y la censura de la misma forma. Ambos callbacks operan únicamente sobre mensajes con `role: "user"`.

### After Model (Post-procesamiento del output)

3. **`eliminar_pensamientos_callback`** — Intercepta la respuesta del LLM y elimina las `parts` marcadas con `thought: true` (razonamiento interno del modelo). Esto garantiza que la interfaz de usuario solo muestre el mensaje final dirigido al usuario, sin exponer el proceso de razonamiento interno.

---

## Estructura del Proyecto

```
smartcities_agent/
├── agent/                    # Directorio del agente (requerido por ADK)
│   ├── __init__.py           # Módulo Python
│   ├── agent.py              # Definición del agente, callbacks e instrucciones
│   ├── tools.py              # Herramientas: plan, presupuesto, búsqueda web, PDF
│   ├── .env                  # Variables de entorno con API keys (NO subir a git)
│   └── .env.example          # Plantilla de variables de entorno
├── output/                   # Directorio donde se genera el PDF (auto-creado)
├── .gitignore
├── requirements.txt
└── README.md
```

> **Importante**: El directorio `agent/` debe contener el archivo `agent.py` con la variable `root_agent` expuesta. Esta es la convención que el servidor ADK necesita para detectar y cargar el agente correctamente.

---

## Requisitos Previos

- **Python 3.10+**
- **Acceso a un LLM** compatible con LiteLLM (por defecto configurado para PoliGPT de la UPV, requiere VPN)
- **pip** para instalar dependencias

---

## Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/smartcities-agent.git
   cd smartcities-agent
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuración

1. **Copiar la plantilla de entorno**:
   ```bash
   cp agent/.env.example agent/.env
   ```

2. **Editar `agent/.env`** con tus claves API:
   ```env
   OPENAI_API_KEY="tu-api-key"
   GOOGLE_API_KEY="tu-google-api-key"    # Opcional si usas Gemini
   ```

3. **Configurar el modelo** (opcional): Si quieres usar otro modelo LLM, edita la línea correspondiente en `agent/agent.py`:
   ```python
   model=LiteLlm(
       model="openai/gpt-4o",           # Cambia el modelo aquí
       api_base="https://api.openai.com/v1/",  # Y la URL base
       api_key="tu-key"
   )
   ```

---

## Uso

### Interfaz Web (Desarrollo y pruebas)

Desde el directorio raíz del proyecto:

```bash
adk web
```

Esto levanta un servidor local en `http://localhost:8000` con la interfaz de desarrollo de ADK donde puedes chatear con el agente.

> **Nota Windows**: Si `adk` no se reconoce como comando, usa la ruta completa del ejecutable dentro del venv:
> ```powershell
> .\venv\Scripts\adk.exe web
> ```

### Evaluación Automática (CLI)

Si dispones de ficheros de evaluación con rúbricas:

```bash
adk eval smartcities_agent ficheros_evaluacion/test_manual_rubric.json \
    --config_file_path=ficheros_evaluacion/test_config.json
```

---

## Ejemplo de Interacción

```
Usuario: Hola, quiero mejorar la movilidad de mi ciudad

Agente: ¡Hola! Como asesor de Ciudades Inteligentes, te puedo sugerir 
           varias funciones para mejorar la movilidad:
           - Semáforos inteligentes con IA adaptativa
           - Sensores de ocupación de aparcamiento
           - Carriles de bus con prioridad semafórica
           ¿Cuáles te interesan?

Usuario: Me gustan los semáforos y los sensores de aparcamiento, adelante

Agente: [Ejecuta automáticamente las 4 herramientas en secuencia]
           
           ¡Genial! He terminado de generar el informe. Lo puedes encontrar
           en un documento PDF con el título: "Plan Integral de Semáforos 
           Inteligentes y Sensores de Aparcamiento". ¡Espero que te sea útil!
```

El PDF generado se encuentra en `output/informe_smartcity_final.pdf`.

---

## Salida Generada

El informe PDF contiene las siguientes secciones:

| Sección | Contenido |
|---------|-----------|
| **Introducción** | Resumen ejecutivo redactado por el LLM sobre el proyecto |
| **Plan de Implementación** | Fases de despliegue detalladas para cada función elegida |
| **Presupuesto** | Desglose financiero: hardware, software y mantenimiento |
| **Conclusiones** | Reflexión del LLM sobre el impacto y beneficios del proyecto |
| **Referencias** | URLs reales obtenidas de búsqueda web |

---

## Evaluación Automática (LLM-as-a-judge)

El agente cuenta con un potente framework de testing automatizado usando el módulo de evaluación de ADK.

Para garantizar la fiabilidad del entorno, la configuración (`test_config.json`) usa identificadores semánticos cortos (`json_validity`, `mandatory_sections`, etc.) y traslada el cuerpo de las rúbricas detalladas al campo *"description"*. Esto evita que durante el proceso de validación, la maleabilidad del texto de salida del LLM juez rompa el mapeo.

**Ejecutar los Test de Evaluación:**
```bash
adk eval agent agent/test_manual_rubric.json --config_file_path=agent/test_config.json
```

**Revisión de Resultados:**
Una vez finaliza el pipeline de testeo, se emitirá un veredicto general en la consola (`Tests passed` / `Tests failed`). Para explorar en detalle las puntuaciones del agente rúbrica a rúbrica, consulta el **historial guardado:**
- **Ruta de salida:** Todos los reportes se tabulan en formato JSON en el directorio `agent/.adk/eval_history/`.
- **Análisis Web:** Puedes iniciar el servidor de desarrollo UI de ADK mediante el comando `adk web`. Dependiendo de tu versión del ADK, el portal local suele contar con un apartado de *"Traces"* o *"Evals"* para consultar de forma visual cómo el Juez IA ha calificado cada métrica sobre 1.0 (o si las catalogó como Failed con un 0).

---

## Autores

- **Andrés Salas Roger**
- **Héctor Zamorano García**

---

## Licencia

Proyecto académico desarrollado para la asignatura AIN — Universitat Politècnica de València (UPV).
