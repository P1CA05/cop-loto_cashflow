"""
Cashflow builder and projector
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def build_cashflow(
    events: List[Dict],
    starting_balance: float,
    horizon_months: int,
    granularity: str = 'weekly',
    safety_threshold: float = 0.0
) -> Tuple[pd.DataFrame, Dict]:
    """
    Build cashflow projection from events
    
    Returns:
    - cashflow_df: DataFrame with columns [period_start, period_end, inflows, outflows, net, balance]
    - kpis: Dict with basic KPIs
    """
    
    if not events:
        logger.warning("No events provided for cashflow")
        # Return empty cashflow
        return _empty_cashflow(), _empty_kpis()
    
    # Convert to DataFrame
    events_df = pd.DataFrame(events)
    events_df['date'] = pd.to_datetime(events_df['date'])
    
    # Define date range
    min_date = events_df['date'].min()
    max_date = events_df['date'].max()
    end_date = datetime.now() + timedelta(days=horizon_months * 30)
    
    # Ensure we cover at least the horizon
    if max_date < end_date:
        max_date = end_date
    
    # Create periods based on granularity
    if granularity == 'daily':
        periods = pd.date_range(start=min_date, end=max_date, freq='D')
    elif granularity == 'weekly':
        periods = pd.date_range(start=min_date, end=max_date, freq='W-MON')
    elif granularity == 'monthly':
        periods = pd.date_range(start=min_date, end=max_date, freq='MS')
    else:
        periods = pd.date_range(start=min_date, end=max_date, freq='W-MON')
    
    # Build cashflow table
    cashflow_data = []
    current_balance = starting_balance
    
    for i in range(len(periods) - 1):
        period_start = periods[i]
        period_end = periods[i + 1]
        
        # Filter events in this period
        period_events = events_df[
            (events_df['date'] >= period_start) & 
            (events_df['date'] < period_end)
        ]
        
        # Calculate inflows and outflows
        inflows = period_events[period_events['amount'] > 0]['amount'].sum()
        outflows = abs(period_events[period_events['amount'] < 0]['amount'].sum())
        net = inflows - outflows
        
        current_balance += net
        
        cashflow_data.append({
            'period_start': period_start,
            'period_end': period_end,
            'inflows': inflows,
            'outflows': outflows,
            'net': net,
            'balance': current_balance,
            'below_safety': current_balance < safety_threshold
        })
    
    cashflow_df = pd.DataFrame(cashflow_data)
    
    # Calculate KPIs
    kpis = _calculate_kpis(cashflow_df, starting_balance, safety_threshold, horizon_months)
    
    logger.info(f"Cashflow generado: {len(cashflow_df)} períodos, balance mínimo: {kpis['min_balance']:.2f}")
    
    return cashflow_df, kpis


def _calculate_kpis(cashflow_df: pd.DataFrame, starting_balance: float, 
                    safety_threshold: float, horizon_months: int) -> Dict:
    """
    Calculate basic KPIs from cashflow
    """
    if len(cashflow_df) == 0:
        return _empty_kpis()
    
    min_balance = cashflow_df['balance'].min()
    min_balance_idx = cashflow_df['balance'].idxmin()
    min_balance_date = cashflow_df.loc[min_balance_idx, 'period_start']
    
    # Calculate risk level
    if min_balance < 0:
        risk_level = 'high'
    elif min_balance < safety_threshold:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    # Calculate runway (weeks until balance < 0)
    negative_periods = cashflow_df[cashflow_df['balance'] < 0]
    if len(negative_periods) > 0:
        first_negative = negative_periods.index[0]
        runway_weeks = first_negative
    else:
        runway_weeks = len(cashflow_df)
    
    # Count safety breaches
    safety_breaches = cashflow_df['below_safety'].sum()
    
    # Calculate burn rate (average weekly outflow)
    avg_outflows = cashflow_df['outflows'].mean()
    
    # Calculate total inflows/outflows
    total_inflows = cashflow_df['inflows'].sum()
    total_outflows = cashflow_df['outflows'].sum()
    
    return {
        'min_balance': float(min_balance),
        'min_balance_date': min_balance_date.strftime('%Y-%m-%d'),
        'risk_level': risk_level,
        'runway_weeks': int(runway_weeks),
        'safety_breaches_count': int(safety_breaches),
        'avg_weekly_burn': float(avg_outflows),
        'total_inflows': float(total_inflows),
        'total_outflows': float(total_outflows),
        'net_position': float(total_inflows - total_outflows),
        'starting_balance': float(starting_balance),
        'ending_balance': float(cashflow_df['balance'].iloc[-1])
    }


def _empty_cashflow() -> pd.DataFrame:
    """Return empty cashflow DataFrame"""
    return pd.DataFrame(columns=['period_start', 'period_end', 'inflows', 'outflows', 'net', 'balance', 'below_safety'])


def _empty_kpis() -> Dict:
    """Return empty KPIs"""
    return {
        'min_balance': 0.0,
        'min_balance_date': 'N/A',
        'risk_level': 'unknown',
        'runway_weeks': 0,
        'safety_breaches_count': 0,
        'avg_weekly_burn': 0.0,
        'total_inflows': 0.0,
        'total_outflows': 0.0,
        'net_position': 0.0,
        'starting_balance': 0.0,
        'ending_balance': 0.0
    }
