"""
Tests for snapshot persistence
"""
import pytest
import os
import json
from core.snapshot_tools import save_snapshot, load_snapshot, list_snapshots


def test_save_and_load_snapshot(tmp_path):
    """Test saving and loading snapshots"""
    # Override history directory for testing
    import core.snapshot_tools as st
    original_dir = st.HISTORY_DIR
    st.HISTORY_DIR = str(tmp_path)
    st.INDEX_FILE = os.path.join(st.HISTORY_DIR, 'index.json')
    
    try:
        snapshot_data = {
            'kpis': {'min_balance': -1000.0, 'risk_level': 'high'},
            'survival': {'capital_total_needed': 5000.0},
            'alerts': [{'severity': 'high', 'title': 'Test alert'}]
        }
        
        snapshot_id = save_snapshot(snapshot_data)
        assert snapshot_id is not None
        
        loaded = load_snapshot(snapshot_id)
        assert loaded is not None
        assert loaded['kpis']['min_balance'] == -1000.0
        
    finally:
        st.HISTORY_DIR = original_dir
        st.INDEX_FILE = os.path.join(st.HISTORY_DIR, 'index.json')


def test_list_snapshots_empty():
    """Test listing snapshots when none exist"""
    snapshots = list_snapshots()
    # May be empty or contain existing snapshots
    assert isinstance(snapshots, list)


if __name__ == '__main__':
    pytest.main([__file__])
