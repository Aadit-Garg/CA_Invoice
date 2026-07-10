from app import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    address = db.Column(db.Text, nullable=False)
    gstin = db.Column(db.String(20))
    pan = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoices = db.relationship('Invoice', backref='client', lazy=True)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Draft') # Draft, Pending, Paid, Overdue
    
    # Client Snapshot
    client_name = db.Column(db.String(150))
    client_address = db.Column(db.Text)
    client_gstin = db.Column(db.String(50))
    client_pan = db.Column(db.String(50))
    
    # Firm Settings Overrides (if null, fall back to global settings)
    firm_name = db.Column(db.String(150))
    firm_address = db.Column(db.Text)
    bank_account_name = db.Column(db.String(150))
    bank_name = db.Column(db.String(150))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))
    
    # Tax configuration
    tax_type = db.Column(db.String(10), default='IGST') # 'IGST' or 'CGST_SGST'
    igst_rate = db.Column(db.Float, default=18.0)
    cgst_rate = db.Column(db.Float, default=9.0)
    sgst_rate = db.Column(db.Float, default=9.0)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('InvoiceItem', backref='invoice', cascade="all, delete-orphan", lazy=True)
    
    @property
    def subtotal(self):
        return sum(item.amount for item in self.items)
        
    @property
    def tax_amount(self):
        if self.tax_type == 'IGST':
            return (self.subtotal * self.igst_rate) / 100
        else:
            return (self.subtotal * (self.cgst_rate + self.sgst_rate)) / 100
            
    @property
    def total_amount(self):
        return self.subtotal + self.tax_amount

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    sac_code = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    # Firm Details
    firm_name = db.Column(db.String(150), default="Sumit N Garg & Associates")
    firm_address = db.Column(db.Text)
    gstin = db.Column(db.String(20))
    pan = db.Column(db.String(20))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    
    # Bank Details
    bank_account_name = db.Column(db.String(150))
    bank_name = db.Column(db.String(150))
    account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))
    branch = db.Column(db.String(150))
    
    # Terms
    default_notes = db.Column(db.Text, default="Thank you for your business.")
