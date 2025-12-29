"""
Quality assessment and data coverage calculator
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def assess_data_quality(
    bank_df: pd.DataFrame,
    sales_invoices_df: pd.DataFrame = None,
    purchase_invoices_df: pd.DataFrame = None,
    warnings: List[str] = None
) -> Dict:
    """
    Assess data quality and coverage
    
    Returns:
    - coverage_months: float
    - confidence_level: 'high', 'medium', 'low'
    - quality_metrics: Dict with details
    - warnings: List of warnings
    """
    
    all_warnings = warnings or []
    
    # Calculate coverage from bank statement
    if len(bank_df) > 0:
        date_range = (bank_df['date'].max() - bank_df['date'].min()).days
        coverage_months = date_range / 30.0
    else:
        coverage_months = 0
        all_warnings.append("⚠️ Sin extracto bancario")
    
    # Calculate parse success rate
    total_files = 1  # Bank is required
    successful_files = 1 if len(bank_df) > 0 else 0
    
    has_sales = sales_invoices_df is not None and len(sales_invoices_df) > 0
    has_purchases = purchase_invoices_df is not None and len(purchase_invoices_df) > 0
    
    if has_sales:
        total_files += 1
        successful_files += 1
    
    if has_purchases:
        total_files += 1
        successful_files += 1
    
    parse_success_rate = successful_files / total_files if total_files > 0 else 0
    
    # Determine confidence level
    confidence_level = _determine_confidence_level(
        coverage_months,
        parse_success_rate,
        has_sales,
        has_purchases,
        len(all_warnings)
    )
    
    quality_metrics = {
        'bank_transactions': len(bank_df),
        'sales_invoices': len(sales_invoices_df) if has_sales else 0,
        'purchase_invoices': len(purchase_invoices_df) if has_purchases else 0,
        'coverage_days': int(date_range) if len(bank_df) > 0 else 0,
        'coverage_months': float(coverage_months),
        'parse_success_rate': float(parse_success_rate),
        'has_future_collections': has_sales,
        'has_future_payments': has_purchases,
        'warnings_count': len(all_warnings)
    }
    
    logger.info(f"Data quality: coverage={coverage_months:.1f} months, confidence={confidence_level}")
    
    return {
        'coverage_months': coverage_months,
        'confidence_level': confidence_level,
        'quality_metrics': quality_metrics,
        'warnings': all_warnings
    }


def _determine_confidence_level(
    coverage_months: float,
    parse_rate: float,
    has_sales: bool,
    has_purchases: bool,
    warnings_count: int
) -> str:
    """
    Determine overall confidence level
    """
    score = 0
    
    # Coverage score (0-3)
    if coverage_months >= 6:
        score += 3
    elif coverage_months >= 3:
        score += 2
    elif coverage_months >= 1:
        score += 1
    
    # Additional data score (0-2)
    if has_sales and has_purchases:
        score += 2
    elif has_sales or has_purchases:
        score += 1
    
    # Parse quality score (0-2)
    if parse_rate >= 0.9:
        score += 2
    elif parse_rate >= 0.7:
        score += 1
    
    # Warnings penalty
    if warnings_count > 5:
        score -= 1
    
    # Determine level
    if score >= 6:
        return 'high'
    elif score >= 3:
        return 'medium'
    else:
        return 'low'
