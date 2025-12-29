"""
KPIs and survival metrics
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def calculate_survival_metrics(
    kpis: Dict,
    horizon_months: int,
    safety_threshold: float,
    credit_line_total: float = 0.0,
    credit_line_used: float = 0.0
) -> Dict:
    """
    Calculate capital needed for survival and recommendations
    
    Returns dict with:
    - capital_total_needed: Total capital to survive horizon
    - capital_propio_recommended: Structural capital (buffer)
    - financiacion_puente_needed: Temporary bridge financing
    - credit_available: Available credit
    - credit_sufficient: bool
    - survival_analysis: detailed breakdown
    """
    
    min_balance = kpis.get('min_balance', 0)
    starting_balance = kpis.get('starting_balance', 0)
    avg_burn = kpis.get('avg_weekly_burn', 0)
    
    # Calculate deficit
    deficit = 0
    if min_balance < 0:
        deficit = abs(min_balance)
    elif min_balance < safety_threshold:
        deficit = safety_threshold - min_balance
    
    # Calculate structural buffer (recommended 1 month of burn)
    structural_buffer = avg_burn * 4  # 4 weeks = 1 month
    
    # Calculate total capital needed
    capital_total_needed = deficit + structural_buffer
    
    # Decompose into own capital vs bridge
    # Rule: structural buffer should be own capital
    # Deficit can be bridge financing
    capital_propio_recommended = structural_buffer
    financiacion_puente_needed = deficit
    
    # Check credit line sufficiency
    credit_available = max(0, credit_line_total - credit_line_used)
    credit_sufficient = credit_available >= financiacion_puente_needed
    credit_gap = max(0, financiacion_puente_needed - credit_available)
    
    survival_analysis = {
        'deficit': float(deficit),
        'structural_buffer': float(structural_buffer),
        'capital_total_needed': float(capital_total_needed),
        'capital_propio_recommended': float(capital_propio_recommended),
        'financiacion_puente_needed': float(financiacion_puente_needed),
        'credit_line_total': float(credit_line_total),
        'credit_line_used': float(credit_line_used),
        'credit_available': float(credit_available),
        'credit_sufficient': credit_sufficient,
        'credit_gap': float(credit_gap),
        'horizon_months': horizon_months,
        'safety_threshold': float(safety_threshold)
    }
    
    logger.info(f"Survival metrics: capital needed={capital_total_needed:.2f}, "
                f"bridge={financiacion_puente_needed:.2f}, gap={credit_gap:.2f}")
    
    return survival_analysis


def enrich_kpis(kpis: Dict, survival_analysis: Dict) -> Dict:
    """
    Combine basic KPIs with survival analysis
    """
    enriched = {**kpis, **survival_analysis}
    return enriched
