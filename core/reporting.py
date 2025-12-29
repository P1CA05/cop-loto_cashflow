"""
Action plan generator
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def generate_action_plan(alerts: List[Dict], kpis: Dict, survival: Dict) -> Dict:
    """
    Generate structured action plan based on alerts and KPIs
    
    Returns dict with timeframes:
    - immediate_48h: List of actions
    - short_term_7_14d: List of actions
    - medium_term_30_90d: List of actions
    """
    
    plan = {
        'immediate_48h': [],
        'short_term_7_14d': [],
        'medium_term_30_90d': []
    }
    
    # IMMEDIATE (48h) - Based on high severity alerts
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    
    if high_alerts:
        for alert in high_alerts[:3]:  # Max 3 immediate actions
            plan['immediate_48h'].append({
                'action': alert['recommended_action'],
                'reason': alert['title'],
                'evidence': alert['evidence']
            })
    else:
        plan['immediate_48h'].append({
            'action': 'Revisar proyección de flujos inmediatos',
            'reason': 'Monitoreo preventivo',
            'evidence': 'Sin alertas críticas'
        })
    
    # If negative balance, add urgent action
    if kpis.get('min_balance', 0) < 0:
        plan['immediate_48h'].insert(0, {
            'action': 'Contactar banco para confirmar disponibilidad de crédito',
            'reason': 'Déficit proyectado',
            'evidence': f"Balance mínimo: {kpis['min_balance']:.2f}€"
        })
    
    # SHORT TERM (7-14 days)
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']
    
    plan['short_term_7_14d'].append({
        'action': 'Revisar y acelerar cobros pendientes prioritarios',
        'reason': 'Optimización de caja',
        'evidence': f"Runway: {kpis.get('runway_weeks', 'N/A')} semanas"
    })
    
    if survival.get('financiacion_puente_needed', 0) > 0:
        plan['short_term_7_14d'].append({
            'action': 'Preparar solicitud de financiación puente',
            'reason': 'Cubrir necesidad temporal',
            'evidence': f"Financiación necesaria: {survival['financiacion_puente_needed']:.2f}€"
        })
    
    if medium_alerts:
        for alert in medium_alerts[:2]:
            plan['short_term_7_14d'].append({
                'action': alert['recommended_action'],
                'reason': alert['title'],
                'evidence': alert['evidence']
            })
    
    # MEDIUM TERM (30-90 days)
    plan['medium_term_30_90d'].append({
        'action': 'Optimizar estructura de costes fijos',
        'reason': 'Mejora de eficiencia',
        'evidence': f"Burn rate: {kpis.get('avg_weekly_burn', 0):.2f}€/semana"
    })
    
    plan['medium_term_30_90d'].append({
        'action': 'Revisar términos de pago con principales clientes',
        'reason': 'Reducir días de cobro',
        'evidence': 'Optimización de ciclo de caja'
    })
    
    if survival.get('capital_propio_recommended', 0) > 0:
        plan['medium_term_30_90d'].append({
            'action': 'Evaluar opciones para aumentar capital estructural',
            'reason': 'Fortalecer posición de caja',
            'evidence': f"Capital recomendado: {survival['capital_propio_recommended']:.2f}€"
        })
    
    logger.info(f"Plan de acción generado: {len(plan['immediate_48h'])} inmediatas, "
                f"{len(plan['short_term_7_14d'])} corto plazo, {len(plan['medium_term_30_90d'])} mediano plazo")
    
    return plan


def format_action_plan_text(plan: Dict) -> str:
    """
    Format action plan as readable text
    """
    text = "## Plan de Acción\n\n"
    
    text += "### 🔴 Inmediato (48 horas)\n\n"
    for i, action in enumerate(plan['immediate_48h'], 1):
        text += f"{i}. **{action['action']}**\n"
        text += f"   - Razón: {action['reason']}\n"
        text += f"   - Evidencia: {action['evidence']}\n\n"
    
    text += "### 🟡 Corto Plazo (7-14 días)\n\n"
    for i, action in enumerate(plan['short_term_7_14d'], 1):
        text += f"{i}. **{action['action']}**\n"
        text += f"   - Razón: {action['reason']}\n\n"
    
    text += "### 🟢 Mediano Plazo (30-90 días)\n\n"
    for i, action in enumerate(plan['medium_term_30_90d'], 1):
        text += f"{i}. **{action['action']}**\n"
        text += f"   - Razón: {action['reason']}\n\n"
    
    return text
