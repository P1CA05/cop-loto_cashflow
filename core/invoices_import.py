"""
Invoices parser (sales and purchase)
"""
import pandas as pd
from datetime import datetime
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


def parse_sales_invoices(file) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse sales invoices
    Expected columns:
    - invoice_id: ID, Número, Number
    - counterparty: Cliente, Customer, Client
    - issue_date: Fecha emisión, Issue Date, Fecha
    - due_date: Fecha vencimiento, Due Date, Vencimiento
    - amount: Importe, Amount
    - status: Estado, Status (paid/unpaid/overdue)
    """
    return _parse_invoices(file, 'sales')


def parse_purchase_invoices(file) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse purchase invoices
    Expected columns similar to sales
    - counterparty: Proveedor, Supplier, Vendor
    """
    return _parse_invoices(file, 'purchase')


def _parse_invoices(file, invoice_type: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Internal parser for invoices
    """
    warnings = []
    
    try:
        # Read file with multiple attempts
        # Handle both Flask FileStorage and regular file objects
        if hasattr(file, 'filename'):
            filename = file.filename.lower()
        elif hasattr(file, 'name'):
            filename = file.name.lower()
        else:
            filename = 'unknown.csv'
        
        df = None
        
        if filename.endswith('.csv'):
            # Try multiple delimiters
            for sep in [',', ';', '\t', '|']:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='utf-8', sep=sep)
                    if len(df.columns) > 1:
                        logger.info(f"CSV leído correctamente con separador '{sep}'")
                        break
                except Exception as e:
                    continue
            
            # Fallback attempts
            if df is None or len(df.columns) == 1:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')
                except Exception as e:
                    pass
            
            # Try different encodings
            if df is None or len(df.columns) == 1:
                for encoding in ['latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, encoding=encoding, sep=',')
                        if len(df.columns) > 1:
                            logger.info(f"CSV leído con encoding '{encoding}'")
                            break
                    except Exception as e:
                        continue
                        
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            raise ValueError("Formato no soportado. Usa CSV o Excel (.xlsx, .xls)")
        
        if df is None:
            raise ValueError("No se pudo leer el archivo")
        
        logger.info(f"Archivo de facturas leído: {len(df)} filas, columnas: {list(df.columns)}")
        
        # Check if parsing failed (single column)
        if len(df.columns) == 1:
            col_name = df.columns[0]
            sample = str(df[col_name].iloc[0])[:100] if len(df) > 0 else ""
            warnings.append(f"⚠️ El archivo no se parseó correctamente. Solo se detectó una columna: '{col_name}'")
            warnings.append(f"⚠️ Muestra: {sample}")
            warnings.append(f"💡 Verifica que el CSV use coma (,) o punto y coma (;) como separador")
            raise ValueError(f"Archivo CSV mal formateado. Columnas: {list(df.columns)}")
        
        logger.info(f"Facturas {invoice_type} leídas: {len(df)} filas")
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Find invoice_id column
        id_col = None
        for col in df.columns:
            if any(term in col for term in ['id', 'número', 'number', 'factura']):
                id_col = col
                break
        
        if id_col:
            df['invoice_id'] = df[id_col].astype(str)
        else:
            df['invoice_id'] = [f"INV-{i+1}" for i in range(len(df))]
            warnings.append("⚠️ No se encontró columna ID, se generaron automáticamente")
        
        # Find counterparty column
        counterparty_col = None
        if invoice_type == 'sales':
            terms = ['cliente', 'customer', 'client']
        else:
            terms = ['proveedor', 'supplier', 'vendor']
        
        for col in df.columns:
            if any(term in col for term in terms):
                counterparty_col = col
                break
        
        if counterparty_col:
            df['counterparty'] = df[counterparty_col].fillna('Desconocido').astype(str)
        else:
            df['counterparty'] = 'Desconocido'
            warnings.append("⚠️ No se encontró columna de contraparte")
        
        # Find issue_date
        issue_col = None
        for col in df.columns:
            if any(term in col for term in ['emisión', 'issue', 'fecha']) and 'venc' not in col:
                issue_col = col
                break
        
        if issue_col:
            df['issue_date'] = pd.to_datetime(df[issue_col], errors='coerce', dayfirst=True)
        else:
            warnings.append("⚠️ No se encontró fecha de emisión")
            df['issue_date'] = pd.NaT
        
        # Find due_date
        due_col = None
        for col in df.columns:
            if any(term in col for term in ['vencimiento', 'due', 'venc']):
                due_col = col
                break
        
        if due_col:
            df['due_date'] = pd.to_datetime(df[due_col], errors='coerce', dayfirst=True)
        else:
            warnings.append("⚠️ No se encontró fecha de vencimiento")
            df['due_date'] = pd.NaT
        
        # Find amount
        amount_col = None
        for col in df.columns:
            if any(term in col for term in ['importe', 'amount', 'total', 'monto']):
                amount_col = col
                break
        
        if amount_col:
            df['amount'] = pd.to_numeric(df[amount_col], errors='coerce')
        else:
            warnings.append("❌ No se encontró columna de importe")
            raise ValueError("Columna de importe no encontrada")
        
        # Find status
        status_col = None
        for col in df.columns:
            if any(term in col for term in ['estado', 'status']):
                status_col = col
                break
        
        if status_col:
            df['status_raw'] = df[status_col].fillna('unknown').astype(str).str.lower()
            # Normalize status
            df['status'] = df['status_raw'].apply(_normalize_status)
        else:
            warnings.append("⚠️ No se encontró columna de estado, asumiendo 'unpaid'")
            df['status'] = 'unpaid'
        
        # Remove invalid rows
        initial_rows = len(df)
        df = df[df['amount'].notna() & (df['amount'] > 0)]
        
        removed = initial_rows - len(df)
        if removed > 0:
            warnings.append(f"⚠️ {removed} facturas sin importe válido eliminadas")
        
        # Keep only required columns
        result_df = df[['invoice_id', 'counterparty', 'issue_date', 'due_date', 'amount', 'status']].copy()
        
        logger.info(f"Facturas {invoice_type} procesadas: {len(result_df)}")
        
        return result_df, warnings
        
    except Exception as e:
        logger.error(f"Error parsing {invoice_type} invoices: {e}")
        warnings.append(f"❌ Error: {str(e)}")
        raise


def _normalize_status(status_str: str) -> str:
    """
    Normalize status values
    """
    status_str = status_str.lower().strip()
    
    if any(term in status_str for term in ['pagada', 'paid', 'cobrada']):
        return 'paid'
    elif any(term in status_str for term in ['vencida', 'overdue', 'atrasada']):
        return 'overdue'
    elif any(term in status_str for term in ['pendiente', 'unpaid', 'impaga']):
        return 'unpaid'
    else:
        return 'unknown'
