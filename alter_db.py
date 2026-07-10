import sqlite3

def upgrade_db():
    conn = sqlite3.connect('invoice.db')
    cursor = conn.cursor()
    
    columns = [
        ('client_name', 'VARCHAR(150)'),
        ('client_address', 'TEXT'),
        ('client_gstin', 'VARCHAR(50)'),
        ('client_pan', 'VARCHAR(50)'),
        ('firm_name', 'VARCHAR(150)'),
        ('firm_address', 'TEXT'),
        ('bank_account_name', 'VARCHAR(150)'),
        ('bank_name', 'VARCHAR(150)'),
        ('account_number', 'VARCHAR(50)'),
        ('ifsc_code', 'VARCHAR(20)')
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            print(f"Skipped column {col_name}: {e}")
            
    conn.commit()
    conn.close()
    print("Database upgrade complete.")

if __name__ == '__main__':
    upgrade_db()
