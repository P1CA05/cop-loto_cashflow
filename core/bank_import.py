"""
Bank statement parser
"""
import pandas as pd
from datetime import datetime
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


def parse_bank_file(file) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse bank statement from CSV or Excel
    Returns: (normalized_df, warnings)
    
    Expected columns (flexible naming):
    - date: Fecha, Date, fecha
    - amount: Importe, Amount, Monto, importe
    - description: Concepto, Description, Descripción, concepto
    
    Or separate columns:
    - debit: Débito, Debit, Cargo
    - credit: Crédito, Credit, Abono
    """
    warnings = []
    
    try:
        # Read file with multiple attempts
        filename = file.filename.lower()
        df = None
        
        if filename.endswith('.csv'):
            # Try multiple delimiters
            for sep in [',', ';', '\t', '|']:
                try:
                    file.seek(0)  # Reset file pointer
                    df = pd.read_csv(file, encoding='utf-8', sep=sep)
                    # Check if we got multiple columns (success)
                    if len(df.columns) > 1:
                        logger.info(f"CSV leído correctamente con separador '{sep}'")
                        break
                except Exception as e:
                    continue
            
            # If still one column, try engine='python' with sep=None
            if df is None or len(df.columns) == 1:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')
                except Exception as e:
                    pass
            
            # Last attempt: try different encodings
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
        
        logger.info(f"Archivo leído: {len(df)} filas, columnas: {list(df.columns)}")
        
        # Check if we only got one column (parsing failed)
        if len(df.columns) == 1:
            col_name = df.columns[0]
            sample = str(df[col_name].iloc[0])[:100] if len(df) > 0 else ""
            warnings.append(f"⚠️ El archivo no se parseó correctamente. Se detectó una sola columna: '{col_name}'")
            warnings.append(f"⚠️ Muestra de datos: {sample}")
            warnings.append(f"💡 Asegúrate de que el CSV use coma (,) o punto y coma (;) como separador")
            raise ValueError(f"El archivo CSV no está correctamente formateado. Columnas detectadas: {list(df.columns)}")
        
        # Normalize column names (lowercase, strip spaces)
        df.columns = df.columns.str.strip().str.lower()
        
        # Find date column
        date_col = None
        for col in df.columns:
            if any(term in col for term in ['fecha', 'date']):
                date_col = col
                break
        
        if date_col is None:
            warnings.append("⚠️ No se encontró columna de fecha (fecha/date)")
            raise ValueError("Columna de fecha no encontrada")
        
        # Find amount columns
        amount_col = None
        debit_col = None
        credit_col = None
        
        for col in df.columns:
            if any(term in col for term in ['importe', 'amount', 'monto']) and 'total' not in col:
                amount_col = col
            elif any(term in col for term in ['débito', 'debit', 'cargo']):
                debit_col = col
            elif any(term in col for term in ['crédito', 'credit', 'abono', 'ingreso']):
                credit_col = col
        
        # Find description column
        desc_col = None
        for col in df.columns:
            if any(term in col for term in ['concepto', 'description', 'descripción', 'detalle']):
                desc_col = col
                break
        
        if desc_col is None:
            # Use first non-numeric column as description
            for col in df.columns:
                if col not in [date_col, amount_col, debit_col, credit_col]:
                    if df[col].dtype == 'object':
                        desc_col = col
                        break
        
        if desc_col is None:
            desc_col = 'description'
            df[desc_col] = 'Sin descripción'
        
        # Parse dates
        try:
            df['date'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")
            warnings.append(f"⚠️ Error procesando fechas: {str(e)}")
            raise
        
        # Check invalid dates
        invalid_dates = df['date'].isna().sum()
        if invalid_dates > 0:
            warnings.append(f"⚠️ {invalid_dates} fechas inválidas eliminadas")
            df = df[df['date'].notna()]
        
        # Parse amounts
        if amount_col:
            # Single amount column
            df['amount'] = pd.to_numeric(df[amount_col], errors='coerce')
        elif debit_col and credit_col:
            # Separate debit/credit columns
            df['debit'] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
            df['credit'] = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)
            df['amount'] = df['credit'] - df['debit']
        else:
            warnings.append("⚠️ No se encontraron columnas de importes")
            raise ValueError("Columnas de importes no encontradas")
        
        # Check invalid amounts
        invalid_amounts = df['amount'].isna().sum()
        if invalid_amounts > 0:
            warnings.append(f"⚠️ {invalid_amounts} importes inválidos eliminados")
            df = df[df['amount'].notna()]
        
        # Normalize description
        df['description'] = df[desc_col].fillna('Sin descripción').astype(str)
        
        # Keep only required columns
        result_df = df[['date', 'amount', 'description']].copy()
        
        # Sort by date
        result_df = result_df.sort_values('date')
        
        # Check for duplicates
        duplicates = result_df.duplicated(subset=['date', 'amount'], keep='first').sum()
        if duplicates > 0:
            warnings.append(f"⚠️ {duplicates} posibles transacciones duplicadas detectadas")
        
        logger.info(f"Extracto procesado: {len(result_df)} transacciones válidas")
        
        if len(result_df) == 0:
            warnings.append("⚠️ No se encontraron transacciones válidas")
            raise ValueError("Sin transacciones válidas")
        
        return result_df, warnings
        
    except Exception as e:
        logger.error(f"Error parsing bank file: {e}")
        warnings.append(f"❌ Error crítico: {str(e)}")
        raise
