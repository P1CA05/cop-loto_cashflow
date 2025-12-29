"""
Tests for cashflow builder
"""
import pytest
from datetime import datetime, timedelta
from core.cashflow import build_cashflow


def test_build_cashflow_basic():
    """Test basic cashflow generation"""
    events = [
        {
            'date': datetime(2025, 1, 1),
            'amount': 1000.0,
            'direction': 'inflow',
            'source': 'bank',
            'description': 'Income',
            'confidence': 'high'
        },
        {
            'date': datetime(2025, 1, 15),
            'amount': -500.0,
            'direction': 'outflow',
            'source': 'bank',
            'description': 'Payment',
            'confidence': 'high'
        }
    ]
    
    cashflow_df, kpis = build_cashflow(events, 5000.0, 3, 'weekly', 1000.0)
    
    assert len(cashflow_df) > 0
    assert 'balance' in cashflow_df.columns
    assert kpis['starting_balance'] == 5000.0
    assert kpis['min_balance'] <= 5000.0 + 1000.0 - 500.0


def test_build_cashflow_negative_balance():
    """Test risk detection with negative balance"""
    events = [
        {
            'date': datetime(2025, 1, 15),
            'amount': -6000.0,
            'direction': 'outflow',
            'source': 'bank',
            'description': 'Large payment',
            'confidence': 'high'
        }
    ]
    
    cashflow_df, kpis = build_cashflow(events, 5000.0, 3, 'weekly', 1000.0)
    
    assert kpis['min_balance'] < 0
    assert kpis['risk_level'] == 'high'


def test_build_cashflow_empty():
    """Test handling of empty events"""
    cashflow_df, kpis = build_cashflow([], 5000.0, 3, 'weekly', 1000.0)
    
    assert len(cashflow_df) == 0
    assert kpis['starting_balance'] == 5000.0


if __name__ == '__main__':
    pytest.main([__file__])
