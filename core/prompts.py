"""
LLM prompt builder with anti-hallucination rules
"""
from typing import Dict, Optional
import json


def build_prompt_initial(payload: Dict) -> str:
    """
    Build initial analysis prompt with strict anti-hallucination rules
    
    Payload should contain:
    - kpis: Dict
    - survival: Dict
    - alerts: List[Dict]
    - scenarios: Dict (optional)
    - coverage_months: float
    - confidence_level: str
    """
    
    # Extract key data
    kpis = payload.get('kpis', {})
    survival = payload.get('survival', {})
    alerts = payload.get('alerts', [])
    coverage = payload.get('coverage_months', 0)
    confidence = payload.get('confidence_level', 'unknown')
    
    # Build structured prompt
    prompt = f"""Eres un asesor financiero especializado en supervivencia empresarial para PYMEs.

Tu tarea es explicar el análisis de cashflow de forma MUY SIMPLE, como si hablaras con alguien sin conocimientos de economía.

ESTILO DE COMUNICACIÓN:
- Usa un lenguaje cercano y sencillo (evita tecnicismos o explícalos)
- Usa analogías y ejemplos del día a día
- Usa emojis para hacer el texto más visual: 💰 📊 ⚠️ ✅ 🎯
- Divide el informe en secciones claras con títulos descriptivos
- Prioriza lo MÁS IMPORTANTE primero

REGLAS CRÍTICAS (no negociables):
1. NUNCA inventes números, fechas, nombres de clientes, proyectos o importes
2. SOLO usa datos explícitos del análisis proporcionado
3. Si un dato no está disponible, di "dato no disponible" o "información insuficiente"
4. NO recalcules números - solo interpreta los proporcionados
5. Cada recomendación DEBE citar evidencia del análisis (KPI, alerta o tabla)
6. Si la cobertura es < 3 meses, NO hables de estacionalidad ni tendencias anuales

DATOS DEL ANÁLISIS:

**Cobertura de Datos:**
- Meses cubiertos: {coverage}
- Nivel de confianza: {confidence}

**KPIs Clave:**
- Saldo mínimo proyectado: {kpis.get('min_balance', 'N/A')}€ (fecha: {kpis.get('min_balance_date', 'N/A')})
- Nivel de riesgo: {kpis.get('risk_level', 'N/A')}
- Runway: {kpis.get('runway_weeks', 'N/A')} semanas
- Burn rate semanal promedio: {kpis.get('avg_weekly_burn', 'N/A')}€
- Ingresos totales proyectados: {kpis.get('total_inflows', 'N/A')}€
- Pagos totales proyectados: {kpis.get('total_outflows', 'N/A')}€

**Análisis de Supervivencia:**
- Capital total necesario: {survival.get('capital_total_needed', 'N/A')}€
- Capital propio recomendado: {survival.get('capital_propio_recommended', 'N/A')}€
- Financiación puente necesaria: {survival.get('financiacion_puente_needed', 'N/A')}€
- Línea de crédito disponible: {survival.get('credit_available', 'N/A')}€
- ¿Crédito suficiente?: {survival.get('credit_sufficient', 'N/A')}
- Brecha de financiación: {survival.get('credit_gap', 'N/A')}€

**Alertas Detectadas:**
"""
    
    if alerts:
        for i, alert in enumerate(alerts, 1):
            prompt += f"\n{i}. [{alert['severity'].upper()}] {alert['title']}"
            prompt += f"\n   {alert['message']}"
            prompt += f"\n   Evidencia: {alert['evidence']}"
            prompt += f"\n   Acción recomendada: {alert['recommended_action']}\n"
    else:
        prompt += "\nNo se detectaron alertas críticas.\n"
    
    prompt += """
INSTRUCCIONES:
Genera un informe ejecutivo estructurado con estas secciones:

1. **Resumen Ejecutivo** (2-3 frases sobre la situación general)
2. **Diagnóstico de Riesgo** (interpretación del nivel de riesgo citando KPIs)
3. **Necesidades de Capital** (explicar capital propio vs financiación puente)
4. **Prioridades de Acción** (basado en alertas, ordenadas por urgencia)
5. **Limitaciones del Análisis** (mencionar cobertura y confianza)

Formato: Markdown, máximo 400 palabras, lenguaje directo y profesional.
"""
    
    return prompt


def build_prompt_refined(payload: Dict, refine_answers: Dict) -> str:
    """
    Build refined prompt incorporating user's answers to guided questions
    
    refine_answers expected keys:
    - priorities: List[str] (checked priorities)
    - timing: str (select value)
    - control: str (radio value)
    - upcoming_cashflows: str (optional textarea)
    - can_renegotiate: str (optional yes/no)
    """
    
    base_prompt = build_prompt_initial(payload)
    
    refinement = "\n\n---\n\n**INFORMACIÓN ADICIONAL DEL USUARIO:**\n\n"
    
    priorities = refine_answers.get('priorities', [])
    if priorities:
        refinement += f"Prioridades del negocio: {', '.join(priorities)}\n"
    
    timing = refine_answers.get('timing', '')
    if timing:
        refinement += f"Situación de cobros: {timing}\n"
    
    control = refine_answers.get('control', '')
    if control:
        refinement += f"Control percibido sobre flujos: {control}\n"
    
    upcoming = refine_answers.get('upcoming_cashflows', '')
    if upcoming:
        refinement += f"Cobros/Pagos grandes próximos: {upcoming}\n"
    
    renegotiate = refine_answers.get('can_renegotiate', '')
    if renegotiate:
        refinement += f"Posibilidad de renegociar pagos: {renegotiate}\n"
    
    refinement += """
**NUEVA TAREA:**
Actualiza SOLO las secciones "Prioridades de Acción" y "Resumen Ejecutivo" considerando 
esta nueva información del usuario. 

IMPORTANTE: NO cambies ningún número ni KPI. Solo ajusta prioridades y recomendaciones 
según el contexto adicional.
"""
    
    return base_prompt + refinement


def build_rules_based_report(payload: Dict) -> str:
    """
    Generate a basic report without LLM (fallback)
    """
    kpis = payload.get('kpis', {})
    survival = payload.get('survival', {})
    alerts = payload.get('alerts', [])
    coverage = payload.get('coverage_months', 0)
    confidence = payload.get('confidence_level', 'unknown')
    
    report = f"""# Informe de Supervivencia Financiera

## Resumen Ejecutivo

Análisis generado con cobertura de {coverage:.1f} meses y nivel de confianza {confidence}.

**Situación de caja:**
- Saldo mínimo proyectado: {kpis.get('min_balance', 0):.2f}€
- Nivel de riesgo: {kpis.get('risk_level', 'unknown').upper()}
- Runway estimado: {kpis.get('runway_weeks', 0)} semanas

**Necesidades de capital:**
- Total necesario: {survival.get('capital_total_needed', 0):.2f}€
- Capital propio recomendado: {survival.get('capital_propio_recommended', 0):.2f}€
- Financiación puente: {survival.get('financiacion_puente_needed', 0):.2f}€

"""
    
    if survival.get('credit_gap', 0) > 0:
        report += f"⚠️ **BRECHA:** Falta {survival['credit_gap']:.2f}€ adicional incluso con línea de crédito.\n\n"
    
    report += "## Alertas Principales\n\n"
    
    if alerts:
        high_alerts = [a for a in alerts if a['severity'] == 'high']
        if high_alerts:
            report += "**CRÍTICAS:**\n"
            for alert in high_alerts:
                report += f"- {alert['title']}: {alert['message']}\n"
        
        medium_alerts = [a for a in alerts if a['severity'] == 'medium']
        if medium_alerts:
            report += "\n**MODERADAS:**\n"
            for alert in medium_alerts[:3]:  # Max 3
                report += f"- {alert['title']}\n"
    else:
        report += "No se detectaron alertas críticas en este momento.\n"
    
    report += "\n## Acciones Recomendadas\n\n"
    report += "**Inmediato (48h):**\n"
    if alerts:
        for alert in alerts[:2]:
            report += f"- {alert['recommended_action']}\n"
    else:
        report += "- Monitorear situación actual\n"
    
    report += "\n**Corto plazo (7-14 días):**\n"
    report += "- Revisar proyección de cobros pendientes\n"
    report += "- Contactar clientes con facturas vencidas\n"
    
    report += "\n**Mediano plazo (30-90 días):**\n"
    report += "- Optimizar estructura de costes\n"
    report += "- Evaluar opciones de financiación\n"
    
    report += f"\n---\n*Informe generado automáticamente (modo rules-based). Cobertura: {coverage:.1f} meses, Confianza: {confidence}.*\n"
    
    return report
