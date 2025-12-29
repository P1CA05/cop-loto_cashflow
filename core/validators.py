"""
Input validation utilities
"""
from typing import Optional, Tuple
import pandas as pd


def validate_float(value, field_name: str, min_value: Optional[float] = None, 
                   allow_none: bool = False) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Validate a float input
    Returns: (is_valid, error_message, parsed_value)
    """
    if value is None or value == '':
        if allow_none:
            return True, None, None
        return False, f"{field_name} es obligatorio", None
    
    try:
        parsed = float(value)
        if min_value is not None and parsed < min_value:
            return False, f"{field_name} debe ser al menos {min_value}", None
        return True, None, parsed
    except (ValueError, TypeError):
        return False, f"{field_name} debe ser un número válido", None


def validate_file(file, allowed_extensions: list = None) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file
    """
    if file is None:
        return False, "No se proporcionó archivo"
    
    if allowed_extensions:
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False, f"Formato no válido. Permitido: {', '.join(allowed_extensions)}"
    
    return True, None


def validate_horizon(horizon_months) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate survival horizon
    """
    try:
        months = int(horizon_months)
        if months not in [3, 6, 9, 12]:
            return False, "Horizonte debe ser 3, 6, 9 o 12 meses", None
        return True, None, months
    except (ValueError, TypeError):
        return False, "Horizonte inválido", None


def validate_granularity(granularity: str) -> Tuple[bool, Optional[str], str]:
    """
    Validate time granularity
    """
    valid = ['daily', 'weekly', 'monthly']
    if granularity not in valid:
        return False, f"Granularidad debe ser una de: {', '.join(valid)}", 'weekly'
    return True, None, granularity


def sanitize_dataframe(df: pd.DataFrame, required_columns: list) -> Tuple[pd.DataFrame, list]:
    """
    Remove invalid rows and return warnings
    """
    warnings = []
    initial_rows = len(df)
    
    # Drop rows with all NaN
    df = df.dropna(how='all')
    
    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        warnings.append(f"Columnas faltantes: {', '.join(missing_cols)}")
    
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        warnings.append(f"{rows_dropped} filas vacías eliminadas")
    
    return df, warnings
