"""
Bridge financing calculator
"""
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calculate_credit_usage(
    cashflow_df: pd.DataFrame,
    credit_line_total: float,
    credit_line_used: float,
    interest_rate_annual: float = 0.0
) -> Dict:
    """
    Simulate credit line usage throughout cashflow periods
    
    Returns:
    - usage_timeline: List of dicts with period, credit_used, credit_available
    - max_usage: Peak credit usage
    - max_usage_date: When peak occurs
    - usage_duration_weeks: How many weeks credit is used
    - estimated_interest_cost: Approximate interest cost
    """
    
    if credit_line_total == 0:
        return _empty_credit_usage()
    
    credit_available = credit_line_total - credit_line_used
    current_credit_used = credit_line_used
    
    usage_timeline = []
    periods_using_credit = 0
    max_usage = credit_line_used
    max_usage_date = None
    total_usage_amount_weeks = 0  # For interest calculation
    
    for _, row in cashflow_df.iterrows():
        balance = row['balance']
        period_start = row['period_start']
        
        # If balance would go negative without credit, use credit
        if balance < 0:
            needed_credit = abs(balance)
            if current_credit_used + needed_credit <= credit_line_total:
                current_credit_used += needed_credit
            else:
                current_credit_used = credit_line_total
        
        # Track max usage
        if current_credit_used > max_usage:
            max_usage = current_credit_used
            max_usage_date = period_start
        
        # Track periods using credit
        if current_credit_used > credit_line_used:
            periods_using_credit += 1
            total_usage_amount_weeks += current_credit_used
        
        usage_timeline.append({
            'period': period_start.strftime('%Y-%m-%d'),
            'credit_used': float(current_credit_used),
            'credit_available': float(credit_line_total - current_credit_used)
        })
    
    # Calculate estimated interest
    # Simple model: average usage * rate * duration
    if periods_using_credit > 0:
        avg_usage = total_usage_amount_weeks / periods_using_credit
        duration_years = periods_using_credit / 52  # Assuming weekly periods
        estimated_interest = avg_usage * (interest_rate_annual / 100) * duration_years
    else:
        estimated_interest = 0
    
    usage_pct = (max_usage / credit_line_total * 100) if credit_line_total > 0 else 0
    
    result = {
        'usage_timeline': usage_timeline[:10],  # First 10 periods only for brevity
        'max_usage': float(max_usage),
        'max_usage_date': max_usage_date.strftime('%Y-%m-%d') if max_usage_date else 'N/A',
        'max_usage_pct': float(usage_pct),
        'usage_duration_weeks': int(periods_using_credit),
        'estimated_interest_cost': float(estimated_interest),
        'credit_line_total': float(credit_line_total),
        'credit_line_used_initially': float(credit_line_used)
    }
    
    logger.info(f"Credit usage: max={max_usage:.2f} ({usage_pct:.1f}%), "
                f"duration={periods_using_credit} weeks, interest~{estimated_interest:.2f}")
    
    return result


def _empty_credit_usage() -> Dict:
    """Return empty credit usage"""
    return {
        'usage_timeline': [],
        'max_usage': 0.0,
        'max_usage_date': 'N/A',
        'max_usage_pct': 0.0,
        'usage_duration_weeks': 0,
        'estimated_interest_cost': 0.0,
        'credit_line_total': 0.0,
        'credit_line_used_initially': 0.0
    }
