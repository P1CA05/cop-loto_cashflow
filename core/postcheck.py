"""
Post-check LLM output for hallucinations
"""
import re
import logging
from typing import Dict, Tuple, List

logger = logging.getLogger(__name__)


def postcheck_report(llm_report: str, payload: Dict) -> Tuple[str, List[str]]:
    """
    Check LLM report for potential hallucinations
    
    Returns:
    - cleaned_report: Report with suspicious numbers flagged
    - warnings: List of warnings found
    """
    
    warnings = []
    
    # Extract known numbers from payload
    known_numbers = _extract_known_numbers(payload)
    
    # Extract numbers from LLM report
    report_numbers = _extract_numbers_from_text(llm_report)
    
    # Check for unknown numbers
    suspicious = []
    for num_str, num_val in report_numbers:
        if not _is_number_known(num_val, known_numbers, tolerance=0.1):
            suspicious.append(num_str)
    
    if suspicious:
        warnings.append(f"⚠️ Números no verificados detectados: {len(suspicious)}")
        logger.warning(f"Suspicious numbers in LLM report: {suspicious[:5]}")
        
        # Flag suspicious numbers in report
        cleaned_report = llm_report
        for num_str in suspicious[:10]:  # Limit to avoid too many replacements
            # Only flag if number is significant (> 10)
            try:
                if abs(float(num_str.replace('€', '').replace(',', ''))) > 10:
                    cleaned_report = cleaned_report.replace(num_str, f"{num_str}*", 1)
            except:
                pass
        
        if len(suspicious) > 0:
            cleaned_report += "\n\n*Nota: Números marcados con * no fueron verificados en el análisis original.*"
    else:
        cleaned_report = llm_report
    
    # Check for forbidden phrases
    forbidden = ['recalculando', 'he calculado', 'mi estimación', 'aproximadamente calculado']
    for phrase in forbidden:
        if phrase.lower() in llm_report.lower():
            warnings.append(f"⚠️ Frase sospechosa detectada: '{phrase}'")
    
    logger.info(f"Post-check complete: {len(warnings)} warnings")
    
    return cleaned_report, warnings


def _extract_known_numbers(payload: Dict) -> List[float]:
    """
    Extract all numbers from payload (KPIs, survival, alerts)
    """
    numbers = []
    
    def extract_from_dict(d):
        for key, value in d.items():
            if isinstance(value, (int, float)):
                numbers.append(float(value))
            elif isinstance(value, dict):
                extract_from_dict(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        extract_from_dict(item)
    
    extract_from_dict(payload)
    return numbers


def _extract_numbers_from_text(text: str) -> List[Tuple[str, float]]:
    """
    Extract numbers from text
    Returns list of (original_string, numeric_value)
    """
    # Pattern for numbers with optional € and thousand separators
    pattern = r'[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?€?'
    
    matches = re.findall(pattern, text)
    results = []
    
    for match in matches:
        try:
            # Clean and parse
            cleaned = match.replace('€', '').replace('.', '').replace(',', '.')
            value = float(cleaned)
            if abs(value) > 0.01:  # Ignore very small numbers
                results.append((match, value))
        except:
            pass
    
    return results


def _is_number_known(num: float, known_numbers: List[float], tolerance: float = 0.1) -> bool:
    """
    Check if number is in known numbers (with tolerance)
    """
    for known in known_numbers:
        if abs(num - known) <= abs(known * tolerance) or abs(num - known) < 1:
            return True
    
    # Also check common derived numbers (sums, differences)
    # For simplicity, we'll be lenient here
    return False
