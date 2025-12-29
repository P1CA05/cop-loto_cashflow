"""
Tests for bank import
"""
import pytest
import pandas as pd
from io import StringIO
from core.bank_import import parse_bank_file


def create_csv_file(content):
    """Helper to create file-like object"""
    from io import BytesIO
    
    class MockFile:
        def __init__(self, content, filename):
            self.content = BytesIO(content.encode('utf-8'))
            self.filename = filename
        
        def read(self):
            return self.content.read()
        
        def seek(self, pos):
            return self.content.seek(pos)
    
    return MockFile(content, 'test.csv')


def test_parse_bank_file_basic():
    """Test basic bank file parsing"""
    csv_content = """Fecha,Importe,Concepto
15/01/2025,1500.00,Cobro cliente
18/01/2025,-850.50,Pago proveedor
20/01/2025,3200.00,Transferencia"""
    
    file = create_csv_file(csv_content)
    df, warnings = parse_bank_file(file)
    
    assert len(df) == 3
    assert 'date' in df.columns
    assert 'amount' in df.columns
    assert 'description' in df.columns
    assert df['amount'].sum() == 1500.00 - 850.50 + 3200.00


def test_parse_bank_file_debit_credit():
    """Test parsing with separate debit/credit columns"""
    csv_content = """Date,Debit,Credit,Description
2025-01-15,0,1500.00,Income
2025-01-18,850.50,0,Payment
2025-01-20,0,3200.00,Transfer"""
    
    file = create_csv_file(csv_content)
    df, warnings = parse_bank_file(file)
    
    assert len(df) == 3
    assert df['amount'].iloc[0] == 1500.00
    assert df['amount'].iloc[1] == -850.50


def test_parse_bank_file_invalid_dates():
    """Test handling of invalid dates"""
    csv_content = """Fecha,Importe,Concepto
15/01/2025,1500.00,Valid
invalid_date,850.50,Invalid
20/01/2025,3200.00,Valid"""
    
    file = create_csv_file(csv_content)
    df, warnings = parse_bank_file(file)
    
    assert len(df) == 2  # Invalid row removed
    assert any('fechas inválidas' in w.lower() for w in warnings)


if __name__ == '__main__':
    pytest.main([__file__])
