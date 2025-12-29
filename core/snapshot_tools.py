"""
Snapshot persistence tools
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

HISTORY_DIR = 'data/history'
INDEX_FILE = os.path.join(HISTORY_DIR, 'index.json')


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects
    """
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def save_snapshot(snapshot_data: Dict, user_id: str = None) -> str:
    """
    Save analysis snapshot to JSON
    
    Args:
        snapshot_data: Snapshot data
        user_id: User ID for multi-user support (optional for backwards compatibility)
    
    Returns: snapshot_id
    """
    
    # Determine directory
    if user_id:
        history_dir = os.path.join('data/history', user_id)
        index_file = os.path.join(history_dir, 'index.json')
    else:
        history_dir = HISTORY_DIR
        index_file = INDEX_FILE
    
    # Ensure directory exists
    os.makedirs(history_dir, exist_ok=True)
    
    # Generate snapshot ID
    snapshot_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Add metadata
    snapshot_data['snapshot_id'] = snapshot_id
    snapshot_data['user_id'] = user_id
    snapshot_data['created_at'] = datetime.now().isoformat()
    snapshot_data['last_updated'] = datetime.now().isoformat()
    snapshot_data['revision'] = 1
    
    # Convert DataFrames to serializable format
    serializable = _prepare_for_serialization(snapshot_data)
    
    # Save snapshot file with custom encoder
    snapshot_file = os.path.join(history_dir, f'{snapshot_id}.json')
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    
    # Update index
    _update_index(snapshot_id, serializable, index_file)
    
    logger.info(f"Snapshot saved: {snapshot_id}")
    
    return snapshot_id


def load_snapshot(snapshot_id: str, user_id: str = None) -> Optional[Dict]:
    """
    Load snapshot by ID
    
    Args:
        snapshot_id: Snapshot ID
        user_id: User ID (optional)
    """
    if user_id:
        history_dir = os.path.join('data/history', user_id)
    else:
        history_dir = HISTORY_DIR
    
    snapshot_file = os.path.join(history_dir, f'{snapshot_id}.json')
    
    if not os.path.exists(snapshot_file):
        logger.error(f"Snapshot not found: {snapshot_id}")
        return None
    
    try:
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Snapshot loaded: {snapshot_id}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading snapshot {snapshot_id}: {e}")
        return None


def update_snapshot(snapshot_id: str, updates: Dict, user_id: str = None) -> bool:
    """
    Update existing snapshot (for refinement)
    
    Args:
        snapshot_id: Snapshot ID
        updates: Updates dict
        user_id: User ID (optional)
    """
    snapshot = load_snapshot(snapshot_id, user_id)
    
    if not snapshot:
        return False
    
    # Update fields
    snapshot.update(updates)
    snapshot['last_updated'] = datetime.now().isoformat()
    snapshot['revision'] = snapshot.get('revision', 1) + 1
    
    # Determine directory
    if user_id:
        history_dir = os.path.join('data/history', user_id)
        index_file = os.path.join(history_dir, 'index.json')
    else:
        history_dir = HISTORY_DIR
        index_file = INDEX_FILE
    
    # Save
    snapshot_file = os.path.join(history_dir, f'{snapshot_id}.json')
    serializable = _prepare_for_serialization(snapshot)
    
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    
    # Update index
    _update_index(snapshot_id, serializable, index_file)
    
    logger.info(f"Snapshot updated: {snapshot_id} (rev {snapshot['revision']})")
    
    return True


def list_snapshots(user_id: str = None) -> List[Dict]:
    """
    List all snapshots from index
    
    Args:
        user_id: User ID (optional)
    """
    if user_id:
        index_file = os.path.join('data/history', user_id, 'index.json')
    else:
        index_file = INDEX_FILE
    
    if not os.path.exists(index_file):
        return []
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Sort by created_at descending
        snapshots = sorted(index.get('snapshots', []), 
                          key=lambda x: x.get('created_at', ''), 
                          reverse=True)
        
        return snapshots
    
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return []


def _update_index(snapshot_id: str, snapshot_data: Dict, index_file: str = INDEX_FILE):
    """
    Update index file with snapshot summary
    
    Args:
        snapshot_id: Snapshot ID
        snapshot_data: Snapshot data
        index_file: Path to index file
    """
    # Load existing index
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {'snapshots': []}
    
    # Create summary
    kpis = snapshot_data.get('kpis', {})
    survival = snapshot_data.get('survival', {})
    
    summary = {
        'snapshot_id': snapshot_id,
        'created_at': snapshot_data.get('created_at'),
        'last_updated': snapshot_data.get('last_updated'),
        'revision': snapshot_data.get('revision', 1),
        'confidence_level': snapshot_data.get('confidence_level', 'unknown'),
        'coverage_months': snapshot_data.get('coverage_months', 0),
        'risk_level': kpis.get('risk_level', 'unknown'),
        'min_balance': kpis.get('min_balance', 0),
        'capital_needed': survival.get('capital_total_needed', 0),
        'credit_gap': survival.get('credit_gap', 0)
    }
    
    # Remove old entry if exists
    index['snapshots'] = [s for s in index['snapshots'] if s['snapshot_id'] != snapshot_id]
    
    # Add new entry
    index['snapshots'].append(summary)
    
    # Save index
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _prepare_for_serialization(data: Dict) -> Dict:
    """
    Convert DataFrames and other non-serializable objects to JSON-serializable format
    Recursively handles all nested structures
    """
    if isinstance(data, dict):
        return {key: _prepare_for_serialization(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_prepare_for_serialization(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(_prepare_for_serialization(item) for item in data)
    elif isinstance(data, pd.DataFrame):
        # Convert DataFrame to list of dicts, handling all types
        df_copy = data.copy()
        # Convert datetime columns to strings
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        # Convert to dict and process recursively
        return [_prepare_for_serialization(row) for row in df_copy.to_dict(orient='records')]
    elif isinstance(data, (pd.Timestamp, datetime)):
        return data.isoformat()
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
        return float(data)
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, np.ndarray):
        return [_prepare_for_serialization(item) for item in data.tolist()]
    elif pd.isna(data):
        return None
    else:
        return data
