"""
Cash events builder - unified view of all cash movements
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def build_events(
    bank_df: pd.DataFrame,
    sales_invoices_df: pd.DataFrame = None,
    purchase_invoices_df: pd.DataFrame = None,
    fixed_costs_monthly: float = None,
    conservative_mode: bool = False
) -> List[Dict]:
    """
    Build unified list of cash events from all sources
    
    Returns list of dicts with:
    - date: datetime
    - amount: float (positive=inflow, negative=outflow)
    - direction: 'inflow' or 'outflow'
    - source: 'bank', 'invoice_sales', 'invoice_purchase', 'fixed_costs'
    - description: str
    - confidence: 'high', 'medium', 'low'
    - invoice_id: optional
    - counterparty: optional
    - status: optional
    """
    events = []
    
    # 1. Bank transactions (HIGH confidence - already happened)
    for _, row in bank_df.iterrows():
        events.append({
            'date': row['date'],
            'amount': row['amount'],
            'direction': 'inflow' if row['amount'] > 0 else 'outflow',
            'source': 'bank',
            'description': row['description'],
            'confidence': 'high',
            'invoice_id': None,
            'counterparty': None,
            'status': 'completed'
        })
    
    # 2. Sales invoices (MEDIUM confidence - future collections)
    if sales_invoices_df is not None and len(sales_invoices_df) > 0:
        for _, row in sales_invoices_df.iterrows():
            if row['status'] == 'paid':
                # Already paid - skip if already in bank (avoid duplicates)
                continue
            
            # Use due_date if available, else issue_date + 30 days
            if pd.notna(row['due_date']):
                event_date = row['due_date']
            elif pd.notna(row['issue_date']):
                event_date = row['issue_date'] + timedelta(days=30)
            else:
                # Skip if no date info
                continue
            
            # Apply conservative mode (delay collections)
            if conservative_mode:
                event_date = event_date + timedelta(days=15)
            
            events.append({
                'date': event_date,
                'amount': row['amount'],
                'direction': 'inflow',
                'source': 'invoice_sales',
                'description': f"Cobro previsto: {row['counterparty']}",
                'confidence': 'medium',
                'invoice_id': row['invoice_id'],
                'counterparty': row['counterparty'],
                'status': row['status']
            })
    
    # 3. Purchase invoices (MEDIUM confidence - future payments)
    if purchase_invoices_df is not None and len(purchase_invoices_df) > 0:
        for _, row in purchase_invoices_df.iterrows():
            if row['status'] == 'paid':
                continue
            
            if pd.notna(row['due_date']):
                event_date = row['due_date']
            elif pd.notna(row['issue_date']):
                event_date = row['issue_date'] + timedelta(days=30)
            else:
                continue
            
            events.append({
                'date': event_date,
                'amount': -abs(row['amount']),  # Negative for outflow
                'direction': 'outflow',
                'source': 'invoice_purchase',
                'description': f"Pago previsto: {row['counterparty']}",
                'confidence': 'medium',
                'invoice_id': row['invoice_id'],
                'counterparty': row['counterparty'],
                'status': row['status']
            })
    
    # 4. Fixed costs (MEDIUM confidence - recurring)
    if fixed_costs_monthly and fixed_costs_monthly > 0:
        # Generate monthly fixed cost events for next 12 months
        start_date = datetime.now()
        for i in range(12):
            event_date = start_date + timedelta(days=30*i)
            events.append({
                'date': event_date,
                'amount': -abs(fixed_costs_monthly),
                'direction': 'outflow',
                'source': 'fixed_costs',
                'description': 'Gastos fijos mensuales',
                'confidence': 'medium',
                'invoice_id': None,
                'counterparty': None,
                'status': 'projected'
            })
    
    logger.info(f"Eventos generados: {len(events)} (bank: {sum(1 for e in events if e['source']=='bank')}, "
                f"sales: {sum(1 for e in events if e['source']=='invoice_sales')}, "
                f"purchases: {sum(1 for e in events if e['source']=='invoice_purchase')}, "
                f"fixed: {sum(1 for e in events if e['source']=='fixed_costs')})")
    
    return events


def events_to_dataframe(events: List[Dict]) -> pd.DataFrame:
    """
    Convert events list to DataFrame for easier manipulation
    """
    if not events:
        return pd.DataFrame(columns=['date', 'amount', 'direction', 'source', 'description', 
                                    'confidence', 'invoice_id', 'counterparty', 'status'])
    
    df = pd.DataFrame(events)
    df = df.sort_values('date')
    return df
