"""
Executive Summary Generator - Ultra-clear decision-focused summary
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def generate_executive_summary(
    kpis: Dict,
    survival: Dict,
    alerts: List[Dict],
    quality_metrics: Dict,
    cashflow_df
) -> Dict:
    """
    Generate ultra-clear executive summary for decision-making
    
    Returns dict with:
    - status: 'low', 'medium', 'high' risk
    - runway_weeks: int
    - runway_months: float
    - action_today: str (immediate action)
    - action_week: str (this week action)
    - missing_data: List[str] (what would improve precision)
    - status_explanation: str
    - confidence_note: str
    """
    
    # Determine global status
    risk_level = kpis.get('risk_level', 'medium')
    
    # Calculate runway
    days_to_zero = kpis.get('days_to_zero_balance', None)
    if days_to_zero and days_to_zero > 0:
        runway_weeks = int(days_to_zero / 7)
        runway_months = round(days_to_zero / 30, 1)
    else:
        runway_weeks = 0
        runway_months = 0
    
    # Get top priority alerts
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']
    
    # Determine immediate action (TODAY)
    if high_alerts:
        action_today = high_alerts[0]['recommended_action']
    elif kpis['min_balance'] < 0:
        action_today = "🚨 Contactar banco/proveedores para negociar plazos - tu saldo llegará a negativo"
    elif survival['financiacion_puente_needed'] > 0:
        action_today = f"💰 Solicitar financiación de {survival['financiacion_puente_needed']:.0f}€ para cubrir déficit proyectado"
    elif medium_alerts:
        action_today = "📞 Revisar cobros pendientes y acelerar facturas vencidas"
    else:
        action_today = "✅ Situación estable - revisar cashflow semanalmente"
    
    # Determine action THIS WEEK
    if risk_level == 'high':
        action_week = "📋 Crear plan de contingencia: lista de gastos reducibles, proveedores negociables, clientes a presionar"
    elif risk_level == 'medium':
        action_week = "📊 Revisar todas las facturas pendientes de cobro y establecer recordatorios de pago"
    else:
        action_week = "💡 Planificar inversiones o reserva de efectivo excedente"
    
    # Missing data recommendations
    missing_data = []
    if quality_metrics.get('coverage_months', 0) < 6:
        missing_data.append(f"Extractos bancarios de más meses (tienes {quality_metrics.get('coverage_months', 0):.1f}, recomendado 6+)")
    if not quality_metrics.get('has_future_collections'):
        missing_data.append("Facturas emitidas pendientes (para proyectar ingresos futuros)")
    if not quality_metrics.get('has_future_payments'):
        missing_data.append("Facturas recibidas pendientes (para proyectar gastos futuros)")
    if not survival.get('fixed_costs_provided'):
        missing_data.append("Gastos fijos mensuales (alquiler, nóminas, etc.)")
    if survival.get('credit_line_total', 0) == 0:
        missing_data.append("Línea de crédito disponible (para calcular capacidad de financiación)")
    
    # Status explanation
    if risk_level == 'high':
        status_explanation = "⚠️ SITUACIÓN CRÍTICA - Requiere acción inmediata"
    elif risk_level == 'medium':
        status_explanation = "⚡ ATENCIÓN NECESARIA - Monitorizar de cerca"
    else:
        status_explanation = "✅ SITUACIÓN SALUDABLE - Mantener seguimiento"
    
    # Confidence note
    confidence = quality_metrics.get('confidence_level', 'medium')
    if confidence == 'high':
        confidence_note = "✅ Alta confianza - Datos completos y consistentes"
    elif confidence == 'medium':
        confidence_note = "⚠️ Confianza media - Algunos datos faltan o son limitados"
    else:
        confidence_note = "⚠️ Confianza baja - Datos insuficientes, proyecciones muy inciertas"
    
    return {
        'status': risk_level,
        'runway_weeks': runway_weeks,
        'runway_months': runway_months,
        'action_today': action_today,
        'action_week': action_week,
        'missing_data': missing_data,
        'status_explanation': status_explanation,
        'confidence_note': confidence_note,
        'min_balance': kpis['min_balance'],
        'min_balance_date': kpis.get('min_balance_date', 'desconocida'),
        'capital_needed': survival.get('capital_total_needed', 0),
        'credit_gap': survival.get('credit_gap', 0)
    }


def format_scenario_changes(scenarios: Dict, has_future_data: bool) -> Dict:
    """
    Explain what changes between scenarios
    
    Returns dict with:
    - base_assumptions: str
    - conservative_changes: str
    - optimistic_changes: str
    - are_different: bool
    """
    
    if not has_future_data:
        return {
            'base_assumptions': 'Proyección basada únicamente en histórico bancario y gastos fijos',
            'conservative_changes': 'Sin cambios (no hay facturas futuras para ajustar)',
            'optimistic_changes': 'Sin cambios (no hay facturas futuras para ajustar)',
            'are_different': False,
            'explanation': 'Los escenarios no difieren significativamente porque no se proporcionaron facturas pendientes de cobro o pago.'
        }
    
    return {
        'base_assumptions': 'Proyección con fechas de cobro/pago tal como están en facturas',
        'conservative_changes': '🔴 Cobros retrasados +15 días, pagos adelantados -7 días (escenario prudente)',
        'optimistic_changes': '🟢 Cobros adelantados -7 días, mantener pagos (escenario favorable)',
        'are_different': True,
        'explanation': 'Los escenarios difieren en el timing de cobros y pagos futuros.'
    }
