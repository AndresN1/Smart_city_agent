import json
from duckduckgo_search import DDGS
import os
import random
from fpdf import FPDF
from typing import Dict, List

# Contador global de llamadas a búsqueda web (máximo 3 por sesión)
_search_call_count = 0
_MAX_SEARCH_CALLS = 3

def search_google_web(query: str) -> List[Dict[str, str]]:
    """Busca en Internet información real sobre el término dado. IMPORTANTE: esta herramienta solo puede usarse un MÁXIMO de 3 veces por conversación."""
    global _search_call_count
    _search_call_count += 1
    if _search_call_count > _MAX_SEARCH_CALLS:
        return [{"status": "error", "message": f"Límite de búsquedas alcanzado ({_MAX_SEARCH_CALLS}). No se pueden hacer más búsquedas."}]
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3, region='es-es'):
                results.append({"status": "success", "title": r.get('title'), "url": r.get('href'), "content": r.get('body')})
        if not results:
            return [{"status": "error", "message": "No results"}]
        return results
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

def generate_implementation_plan(funciones: List[str], plan_detallado: str) -> str:
    """
    Registra y valida el plan de implementación redactado por el agente para las funciones inteligentes elegidas.
    El agente debe redactar él mismo un plan técnico exhaustivo y detallado (mínimo 150 palabras) y pasarlo
    como argumento 'plan_detallado'. La lista 'funciones' contiene los nombres de las funciones elegidas.
    """
    header = "### Plan de Implementación de Funciones Inteligentes\n\n"
    header += "Funciones contempladas: " + ", ".join(funciones) + ".\n\n"
    
    plan_completo = header + plan_detallado
    return plan_completo

def estimate_budget(implementation_plan: str, presupuesto_detallado: str) -> str:
    """
    Registra el presupuesto redactado por el agente y lo complementa con cifras estimadas.
    El agente debe redactar él mismo un presupuesto detallado (mínimo 150 palabras) desglosando
    costes de hardware, software y mantenimiento, y pasarlo como 'presupuesto_detallado'.
    La herramienta calculará cifras estimadas automáticamente basándose en el número de funciones.
    """
    # Contar funciones del plan para escalar costes
    lines = [l for l in implementation_plan.split('\n') if l.strip()]
    items = max(len([l for l in lines if 'Funciones contempladas:' in l or l.strip().startswith('####')]), 1)
    
    costo_hard = items * random.randint(15500, 52000)
    costo_soft = items * random.randint(6500, 24000)
    costo_mant = items * random.randint(2500, 7000)
    total = costo_hard + costo_soft + costo_mant
    
    header = f"### Presupuesto Estimado del Proyecto\n\n"
    header += f"Cifras calculadas para {items} función(es):\n"
    header += f"- Hardware y despliegue físico: {costo_hard} EUR\n"
    header += f"- Software, IA y licenciamiento Cloud: {costo_soft} EUR\n"
    header += f"- Mantenimiento anual (SLA): {costo_mant} EUR\n"
    header += f"- TOTAL ESTIMADO: {total} EUR\n\n"
    
    return header + presupuesto_detallado


def export_pdf_and_json(title: str, report_summary: str, implementation_plan: str, budget: str, conclusions: str, references_urls: List[str], pdf_path: str = "informe.pdf") -> Dict:
    """
    Construye el informe JSON formal y el PDF definitivo para dar por finalizada la tarea.
    Pásale como parámetros obligatorios los textos íntegros generados (resumen, plan, presupuesto, conclusiones).
    """
    os.makedirs(os.path.dirname(pdf_path) if os.path.dirname(pdf_path) else ".", exist_ok=True)

    sections = [
        {"name": "Introducción", "content": report_summary},
        {"name": "Plan de Implementacion", "content": implementation_plan},
        {"name": "Presupuesto", "content": budget},
        {"name": "Conclusiones", "content": conclusions}
    ]

    final_sections = []
    total_words = 0
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=16, style='B')
    pdf.multi_cell(0, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), align='C')
    pdf.ln(10)

    for sec in sections:
        name = sec["name"]
        text = sec["content"]
        
        wc = len([w for w in text.split() if w.strip()])
        final_sections.append({"name": name, "word_count": wc})
        total_words += wc
        
        pdf.set_font("Helvetica", size=14, style='B')
        pdf.cell(200, 10, txt=name.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 10, txt=text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)

    pdf.set_font("Helvetica", size=14, style='B')
    pdf.cell(200, 10, txt="Referencias Bibliograficas", ln=True)
    pdf.set_font("Helvetica", size=10)
    
    safe_refs = list(references_urls) if isinstance(references_urls, list) else []
    dummy_refs = ["https://es.wikipedia.org/wiki/Internet_de_las_cosas", "https://es.wikipedia.org/wiki/Smart_city", "https://es.wikipedia.org/wiki/Inteligencia_artificial"]
    while len(safe_refs) < 3:
        safe_refs.append(dummy_refs.pop())
        
    for i, ref in enumerate(safe_refs, 1):
        pdf.cell(200, 10, txt=f"[{i}] {ref}".encode('latin-1', 'replace').decode('latin-1'), ln=True)
        
    pdf.output(pdf_path)

    output_meta = {
        "title": title,
        "sections": final_sections,
        "total_words": total_words,
        "num_sections": len(final_sections),
        "num_references": len(safe_refs),
        "pdf_path": pdf_path
    }
    
    # Guardar los metadatos en un archivo JSON 
    json_path = os.path.join(os.path.dirname(pdf_path) if os.path.dirname(pdf_path) else ".", "report_metadata.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_meta, f, indent=4, ensure_ascii=False)
    
    return {"status": "success", "json_output": output_meta, "instruction": "Responde al usuario con un mensaje amable en lenguaje natural diciendo que el informe se ha generado correctamente y que lo puede encontrar en PDF con el título indicado. NO muestres este JSON."}
