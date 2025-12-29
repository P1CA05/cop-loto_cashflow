"""
Scenario generator (base, conservative, optimistic)
"""
import pandas as pd
from datetime import timedelta
from typing import Dict, List
import logging
from core.cashflow import build_cashflow
from core.kpis import calculate_survival_metrics

logger = logging.getLogger(__name__)


def generate_scenarios(
    events: List[Dict],
    starting_balance: float,
    horizon_months: int,
    granularity: str,
    safety_threshold: float,
    credit_line_total: float = 0.0,
    credit_line_used: float = 0.0
) -> Dict:
    """
    Generate multiple scenarios: base, conservative, optimistic
    
    Returns dict with scenario_name -> scenario_data
    """
    
    scenarios = {}
    
    # 1. BASE SCENARIO (as-is)
    cashflow_base, kpis_base = build_cashflow(events, starting_balance, horizon_months, 
                                               granularity, safety_threshold)
    survival_base = calculate_survival_metrics(kpis_base, horizon_months, safety_threshold,
                                                credit_line_total, credit_line_used)
    
    scenarios['base'] = {
        'name': 'Escenario Base',
        'description': 'Proyección con datos actuales',
        'cashflow_df': cashflow_base,
        'kpis': kpis_base,
        'survival': survival_base
    }
    
    # Check if we have future collections/payments for meaningful scenarios
    has_future_events = any(e.get('is_future', False) for e in events)
    
    # 2. CONSERVATIVE SCENARIO (delay collections)
    events_conservative = _apply_conservative_adjustments(events)
    
    cashflow_cons, kpis_cons = build_cashflow(events_conservative, starting_balance, 
                                               horizon_months, granularity, safety_threshold)
    survival_cons = calculate_survival_metrics(kpis_cons, horizon_months, safety_threshold,
                                                credit_line_total, credit_line_used)
    
    scenarios['conservative'] = {
        'name': 'Escenario Conservador',
        'description': 'Cobros retrasados +15 días' if has_future_events else 'Basado solo en histórico (sin facturas pendientes)',
        'cashflow_df': cashflow_cons,
        'kpis': kpis_cons,
        'survival': survival_cons,
        'limited': not has_future_events
    }
    
    # 3. OPTIMISTIC SCENARIO (accelerate collections)
    events_optimistic = _apply_optimistic_adjustments(events)
    
    cashflow_opt, kpis_opt = build_cashflow(events_optimistic, starting_balance,
                                             horizon_months, granularity, safety_threshold)
    survival_opt = calculate_survival_metrics(kpis_opt, horizon_months, safety_threshold,
                                               credit_line_total, credit_line_used)
    
    scenarios['optimistic'] = {
        'name': 'Escenario Optimista',
        'description': 'Cobros adelantados parcialmente' if has_future_events else 'Basado solo en histórico (sin facturas pendientes)',
        'cashflow_df': cashflow_opt,
        'kpis': kpis_opt,
        'survival': survival_opt,
        'limited': not has_future_events
    }
    
    logger.info(f"Escenarios generados: base, conservador, optimista")
    
    return scenarios


def _apply_conservative_adjustments(events: List[Dict]) -> List[Dict]:
    """
    Apply conservative adjustments: delay future inflows
    """
    adjusted = []
    for event in events:
        event_copy = event.copy()
        
        # Only adjust future inflows from invoices (not historical bank data)
        if event['direction'] == 'inflow' and event['source'] in ['invoice_sales']:
            # Delay by 15 days
            event_copy['date'] = pd.to_datetime(event['date']) + timedelta(days=15)
        
        adjusted.append(event_copy)
    
    return adjusted


def _apply_optimistic_adjustments(events: List[Dict]) -> List[Dict]:
    """
    Apply optimistic adjustments: accelerate some inflows
    """
    adjusted = []
    for event in events:
        event_copy = event.copy()
        
        # Accelerate 50% of future inflows by 7 days
        if event['direction'] == 'inflow' and event['source'] in ['invoice_sales']:
            # Advance by 7 days (could be made more sophisticated)
            event_copy['date'] = pd.to_datetime(event['date']) - timedelta(days=7)
        
        adjusted.append(event_copy)
    
    return adjusted


def compare_scenarios(scenarios: Dict) -> pd.DataFrame:
    """
    Create comparison table of key metrics across scenarios
    """
    comparison = []
    
    for scenario_key, scenario_data in scenarios.items():
        kpis = scenario_data['kpis']
        survival = scenario_data['survival']
        
        comparison.append({
            'scenario': scenario_data['name'],
            'min_balance': kpis['min_balance'],
            'risk_level': kpis['risk_level'],
            'runway_weeks': kpis['runway_weeks'],
            'capital_needed': survival['capital_total_needed'],
            'bridge_financing': survival['financiacion_puente_needed'],
            'credit_gap': survival['credit_gap']
        })
    
    return pd.DataFrame(comparison)
