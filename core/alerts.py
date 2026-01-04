"""
Alert generator - actionable warnings based on KPIs
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def generate_alerts(kpis: Dict, survival: Dict, cashflow_df, quality_metrics: Dict = None) -> List[Dict]:
    """
    Generate actionable alerts with evidence
    
    Each alert has:
    - severity: 'low', 'medium', 'high'
    - title: Brief headline
    - message: Description
    - evidence: Reference to KPI/data
    - recommended_action: What to do
    """
    
    alerts = []
    
    # 0. DATA QUALITY WARNINGS (if provided)
    if quality_metrics:
        coverage_months = quality_metrics.get('coverage_months', 0)
        if coverage_months < 3:
            alerts.append({
                'severity': 'medium',
                'title': 'Cobertura de Datos Limitada',
                'message': f'Solo {coverage_months:.1f} meses de extracto bancario. No hay datos suficientes para inferir estacionalidad o patrones fiables.',
                'evidence': f'Cobertura: {coverage_months:.1f} meses (recomendado: 6+ meses)',
                'recommended_action': 'Subir extractos bancarios de más meses para mejorar precisión'
            })
        
        if not quality_metrics.get('has_future_collections') and not quality_metrics.get('has_future_payments'):
            alerts.append({
                'severity': 'low',
                'title': 'Sin Facturas Pendientes',
                'message': 'Escenarios conservador/optimista limitados por falta de datos futuros conocidos (facturas pendientes).',
                'evidence': 'No se detectaron facturas emitidas ni recibidas pendientes',
                'recommended_action': 'Subir archivos de facturas emitidas y recibidas para mejorar escenarios futuros'
            })
    
    # 1. Negative balance alert - SIMPLIFICADO Y CLARO
    if kpis['min_balance'] < 0:
        alerts.append({
            'severity': 'high',
            'title': '🚨 ¡ALERTA CRÍTICA! Tu cuenta llegará a números rojos',
            'message': f"Tu saldo bancario caerá a **{kpis['min_balance']:.0f}€** (negativo) alrededor del **{kpis['min_balance_date']}**. "
                      f"Esto significa que no tendrás dinero suficiente para pagar todo lo que tienes pendiente.",
            'evidence': f"Saldo mínimo proyectado: {kpis['min_balance']:.0f}€",
            'recommended_action': '💡 **ACCIÓN URGENTE**: Necesitas conseguir financiación YA o posponer pagos grandes hasta que entren más ingresos. '
                                 'Habla con tu banco sobre ampliar tu línea de crédito o negocia plazos de pago con proveedores.'
        })
    
    # 2. Safety threshold breach - EXPLICACIÓN SENCILLA
    safety_threshold = survival.get('safety_threshold', 0)
    if kpis['min_balance'] > 0 and kpis['min_balance'] < safety_threshold:
        alerts.append({
            'severity': 'medium',
            'title': '⚠️ Tu colchón de seguridad se agotará pronto',
            'message': f"Tu saldo bajará a **{kpis['min_balance']:.0f}€**, que está por debajo de tu colchón de seguridad de **{safety_threshold:.0f}€**. "
                      f"Aunque no llegarás a números rojos, estarás en una zona de riesgo.",
            'evidence': f"Saldo mínimo: {kpis['min_balance']:.0f}€ | Colchón recomendado: {safety_threshold:.0f}€",
            'recommended_action': '💡 **RECOMENDACIÓN**: Revisa tus gastos no urgentes (¿puedes posponer algo?) y acelera el cobro de facturas pendientes.'
        })
    
    # 3. Short runway alert - ANALOGÍA COMPRENSIBLE
    if kpis['runway_weeks'] < 12:  # Less than 3 months
        alerts.append({
            'severity': 'high',
            'title': '⏰ Tiempo limitado: solo tienes {:.0f} semanas de margen'.format(kpis['runway_weeks']),
            'message': f"Si sigues gastando al ritmo actual, en **{kpis['runway_weeks']:.0f} semanas** podrías tener problemas de liquidez. "
                      f"Es como si tu depósito de gasolina solo te durara {kpis['runway_weeks']:.0f} semanas más.",
            'evidence': f"Semanas de supervivencia: {kpis['runway_weeks']:.0f}",
            'recommended_action': '💡 **URGENTE**: Acelera el cobro de facturas pendientes, reduce gastos no esenciales y considera opciones de financiación.'
        })
    elif kpis['runway_weeks'] < 24:  # Less than 6 months
        alerts.append({
            'severity': 'medium',
            'title': '🕐 Margen justo: {:.0f} semanas de autonomía'.format(kpis['runway_weeks']),
            'message': f"Aproximadamente {kpis['runway_weeks']} semanas de margen antes de problemas",
            'evidence': f"KPI: runway_weeks = {kpis['runway_weeks']}",
            'recommended_action': 'Comenzar a buscar opciones de financiación y optimizar cobros'
        })
    
    # 4. High credit dependency
    if survival['credit_line_total'] > 0:
        max_usage_pct = (survival['financiacion_puente_needed'] / survival['credit_line_total'] * 100 
                        if survival['credit_line_total'] > 0 else 0)
        
        if max_usage_pct > 80:
            alerts.append({
                'severity': 'high',
                'title': 'Dependencia Crítica del Crédito',
                'message': f"Se necesitaría usar {max_usage_pct:.1f}% de la línea de crédito",
                'evidence': f"Financiación puente necesaria: {survival['financiacion_puente_needed']:.2f}€, "
                           f"Crédito disponible: {survival['credit_available']:.2f}€",
                'recommended_action': 'Diversificar fuentes de financiación y reducir dependencia'
            })
        elif max_usage_pct > 50:
            alerts.append({
                'severity': 'medium',
                'title': 'Uso Significativo de Crédito',
                'message': f"Se usaría aproximadamente {max_usage_pct:.1f}% de la línea de crédito",
                'evidence': f"Financiación puente: {survival['financiacion_puente_needed']:.2f}€",
                'recommended_action': 'Monitorear uso y preparar plan B si el crédito no es suficiente'
            })
    
    # 5. Credit gap alert
    if survival['credit_gap'] > 0:
        alerts.append({
            'severity': 'high',
            'title': 'Brecha de Financiación',
            'message': f"Falta financiación adicional de {survival['credit_gap']:.2f}€ incluso con la línea de crédito",
            'evidence': f"Gap: {survival['credit_gap']:.2f}€ = Necesidad ({survival['financiacion_puente_needed']:.2f}€) "
                       f"- Crédito disponible ({survival['credit_available']:.2f}€)",
            'recommended_action': 'URGENTE: Buscar capital adicional (inversores, préstamo, aplazamiento pagos)'
        })
    
    # 6. Concentration of payments
    if cashflow_df is not None and len(cashflow_df) > 0:
        max_outflow = cashflow_df['outflows'].max()
        avg_outflow = cashflow_df['outflows'].mean()
        
        if max_outflow > avg_outflow * 2:
            max_outflow_period = cashflow_df.loc[cashflow_df['outflows'].idxmax(), 'period_start'].strftime('%Y-%m-%d')
            alerts.append({
                'severity': 'medium',
                'title': 'Concentración de Pagos',
                'message': f"Pico de pagos de {max_outflow:.2f}€ en período {max_outflow_period} "
                          f"(el doble del promedio {avg_outflow:.2f}€)",
                'evidence': f"Análisis de tabla cashflow: max_outflow = {max_outflow:.2f}€",
                'recommended_action': 'Negociar escalonamiento de pagos grandes o asegurar liquidez temporal'
            })
    
    # 7. Low data coverage warning
    # This would be added by quality.py, but we can check here too
    
    logger.info(f"Alertas generadas: {len(alerts)} ({sum(1 for a in alerts if a['severity']=='high')} críticas)")
    
    return alerts


def prioritize_alerts(alerts: List[Dict]) -> List[Dict]:
    """
    Sort alerts by severity (high first)
    """
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(alerts, key=lambda x: severity_order[x['severity']])
