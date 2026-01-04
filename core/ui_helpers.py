"""
UI Helper Functions - Cashflow filtering, alert drill-down, etc.
"""
import pandas as pd
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def filter_cashflow_periods(cashflow_df, show_only_movement: bool = False, threshold: float = 1.0):
    """
    Filter cashflow to show only periods with significant movement
    
    Args:
        cashflow_df: DataFrame with cashflow
        show_only_movement: If True, hide periods with no activity
        threshold: Minimum absolute value to consider "movement"
    
    Returns: Filtered DataFrame
    """
    if not show_only_movement:
        return cashflow_df
    
    # Keep periods where inflows > threshold OR outflows > threshold
    mask = (cashflow_df['inflows'].abs() > threshold) | (cashflow_df['outflows'].abs() > threshold)
    
    return cashflow_df[mask]


def aggregate_cashflow_monthly(cashflow_df):
    """
    Aggregate daily/weekly cashflow to monthly view
    
    Args:
        cashflow_df: DataFrame with columns [period_start, inflows, outflows, net, balance]
    
    Returns: Monthly aggregated DataFrame
    """
    df = cashflow_df.copy()
    
    # Convert period_start to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df['period_start']):
        df['period_start'] = pd.to_datetime(df['period_start'])
    
    # Extract year-month
    df['month'] = df['period_start'].dt.to_period('M')
    
    # Aggregate
    monthly = df.groupby('month').agg({
        'inflows': 'sum',
        'outflows': 'sum',
        'net': 'sum',
        'balance': 'last'  # Take end-of-month balance
    }).reset_index()
    
    # Format period_start as string
    monthly['period_start'] = monthly['month'].astype(str)
    monthly = monthly.drop(columns=['month'])
    
    # Add below_safety flag (simplified)
    monthly['below_safety'] = False
    
    return monthly


def find_alert_transactions(
    alert: Dict,
    cashflow_df,
    events_df,
    limit: int = 10
) -> List[Dict]:
    """
    Find transactions that triggered a specific alert
    
    Args:
        alert: Alert dictionary
        cashflow_df: Full cashflow DataFrame
        events_df: Events DataFrame with transaction details
        limit: Max transactions to return
    
    Returns: List of transaction dicts with [date, description, amount, source]
    """
    
    transactions = []
    
    # For negative balance alert, find periods around min balance
    if 'negativo' in alert.get('message', '').lower() or 'números rojos' in alert.get('message', '').lower():
        # Find the period with minimum balance
        min_row = cashflow_df[cashflow_df['balance'] == cashflow_df['balance'].min()]
        
        if not min_row.empty:
            min_date = min_row.iloc[0]['period_start']
            
            # Find events around that date (±7 days)
            if not pd.api.types.is_datetime64_any_dtype(events_df['fecha']):
                events_df_copy = events_df.copy()
                events_df_copy['fecha'] = pd.to_datetime(events_df_copy['fecha'], errors='coerce')
            else:
                events_df_copy = events_df
            
            if not pd.api.types.is_datetime64_any_dtype(min_date):
                min_date = pd.to_datetime(min_date)
            
            mask = (events_df_copy['fecha'] >= min_date - pd.Timedelta(days=7)) & \
                   (events_df_copy['fecha'] <= min_date + pd.Timedelta(days=7))
            
            relevant_events = events_df_copy[mask].nlargest(limit, 'importe', keep='all')
            
            for _, row in relevant_events.iterrows():
                transactions.append({
                    'date': row['fecha'].strftime('%Y-%m-%d') if pd.notna(row['fecha']) else 'N/A',
                    'description': row.get('descripcion', 'Sin descripción')[:50],
                    'amount': f"{row['importe']:.2f}€",
                    'source': row.get('origen', 'desconocido')
                })
    
    # For runway alert, show largest outflows
    elif 'runway' in alert.get('title', '').lower() or 'semanas' in alert.get('message', '').lower():
        # Get largest outflows (negative amounts)
        outflow_events = events_df[events_df['importe'] < 0].nsmallest(limit, 'importe')
        
        for _, row in outflow_events.iterrows():
            transactions.append({
                'date': str(row['fecha'])[:10] if pd.notna(row['fecha']) else 'N/A',
                'description': row.get('descripcion', 'Sin descripción')[:50],
                'amount': f"{row['importe']:.2f}€",
                'source': row.get('origen', 'desconocido')
            })
    
    # For other alerts, show mix of largest inflows and outflows
    else:
        large_movements = events_df.nlargest(limit // 2, 'importe', keep='all')
        large_outflows = events_df.nsmallest(limit // 2, 'importe', keep='all')
        combined = pd.concat([large_movements, large_outflows]).drop_duplicates()
        
        for _, row in combined.head(limit).iterrows():
            transactions.append({
                'date': str(row['fecha'])[:10] if pd.notna(row['fecha']) else 'N/A',
                'description': row.get('descripcion', 'Sin descripción')[:50],
                'amount': f"{row['importe']:.2f}€",
                'source': row.get('origen', 'desconocido')
            })
    
    return transactions


def format_capital_breakdown(survival: Dict) -> Dict:
    """
    Break down capital needed into understandable components
    
    Returns dict with clear explanations
    """
    
    deficit = survival.get('deficit', 0)
    buffer = survival.get('structural_buffer', 0)
    capital_total = survival.get('capital_total_needed', 0)
    capital_propio = survival.get('capital_propio_recommended', 0)
    financiacion = survival.get('financiacion_puente_needed', 0)
    
    credit_total = survival.get('credit_line_total', 0)
    credit_available = survival.get('credit_available', 0)
    credit_max_usage = survival.get('credit_max_usage', 0)
    credit_gap = survival.get('credit_gap', 0)
    
    # Interest cost estimation
    interest_rate = survival.get('interest_rate', 0)
    if credit_max_usage > 0 and interest_rate > 0:
        # Estimate monthly interest cost
        monthly_interest = (credit_max_usage * interest_rate / 100) / 12
        # Estimate total interest for duration
        duration_months = survival.get('credit_duration_months', 3)
        total_interest = monthly_interest * duration_months
    else:
        monthly_interest = 0
        total_interest = 0
    
    return {
        'deficit_max': deficit,
        'deficit_explanation': 'Máximo déficit acumulado en el período proyectado (cuánto te faltará en el peor momento)',
        'buffer': buffer,
        'buffer_explanation': 'Colchón de seguridad recomendado para imprevistos (20-30% del déficit)',
        'capital_total': capital_total,
        'capital_total_explanation': 'Déficit + Buffer = Total necesario para sobrevivir el período',
        'capital_propio': capital_propio,
        'capital_propio_explanation': 'Cuánto deberías tener de tu bolsillo (50% del total)',
        'financiacion': financiacion,
        'financiacion_explanation': 'Cuánto necesitas pedir prestado (el resto del total)',
        'credit_available': credit_available,
        'credit_max_usage': credit_max_usage,
        'credit_usage_explanation': f'Usarás máximo {credit_max_usage:.0f}€ de tu línea de crédito',
        'credit_gap': credit_gap,
        'credit_gap_explanation': 'Cuánto te falta de línea de crédito (si es negativo, tienes suficiente)',
        'monthly_interest': monthly_interest,
        'total_interest': total_interest,
        'interest_explanation': f'Coste estimado: {monthly_interest:.0f}€/mes × {survival.get("credit_duration_months", 3)} meses = {total_interest:.0f}€ total'
    }
