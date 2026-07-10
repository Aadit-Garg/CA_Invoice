from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Client, Invoice, InvoiceItem, Settings
from datetime import datetime
import os
import requests
from itsdangerous import URLSafeTimedSerializer

main_bp = Blueprint('main', __name__)

@main_bp.route('/auth/sso')
def auth_sso():
    token = request.args.get('token')
    if not token:
        flash('Invalid SSO request.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    secret = os.environ.get('INVOICE_APP_SECRET')
    if not secret:
        flash('Invoice app not configured for SSO.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    serializer = URLSafeTimedSerializer(secret)
    try:
        data = serializer.loads(token, max_age=300) # 5 minutes expiration
        session['api_url'] = data.get('api_url')
        session['api_key'] = data.get('api_key')
        session['admin_email'] = data.get('admin_email')
        
        # Fetch initial settings from Manage app
        try:
            resp = requests.get(session['api_url'], params={'api_key': session['api_key']}, timeout=5)
            if resp.status_code == 200:
                settings_data = resp.json().get('settings', {})
                if settings_data:
                    session['firm_name'] = settings_data.get('firm_name')
                    session['logo_url'] = settings_data.get('logo_url')
        except:
            pass
            
        flash(f"Secure connection established for {session['admin_email']}.", "success")
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash('Invalid or expired SSO token.', 'danger')
        return redirect(url_for('main.dashboard'))


@main_bp.route('/')
def dashboard():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(10).all()
    clients_count = Client.query.count()
    invoices_count = Invoice.query.count()
    return render_template('dashboard.html', invoices=invoices, clients_count=clients_count, invoices_count=invoices_count)

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    setting = Settings.query.first()
    if not setting:
        setting = Settings()
        db.session.add(setting)
        db.session.commit()
        
    if request.method == 'POST':
        setting.firm_name = request.form.get('firm_name')
        setting.firm_address = request.form.get('firm_address')
        setting.gstin = request.form.get('gstin')
        setting.pan = request.form.get('pan')
        setting.email = request.form.get('email')
        setting.phone = request.form.get('phone')
        setting.bank_account_name = request.form.get('bank_account_name')
        setting.bank_name = request.form.get('bank_name')
        setting.account_number = request.form.get('account_number')
        setting.ifsc_code = request.form.get('ifsc_code')
        setting.branch = request.form.get('branch')
        setting.default_notes = request.form.get('default_notes')
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('main.settings'))
        
    return render_template('settings.html', setting=setting)

@main_bp.route('/clients', methods=['GET'])
def clients():
    all_clients = Client.query.order_by(Client.created_at.desc()).all()
    return render_template('clients.html', clients=all_clients)

@main_bp.route('/clients/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        client = Client(
            name=request.form.get('name'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            gstin=request.form.get('gstin'),
            pan=request.form.get('pan')
        )
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully', 'success')
        return redirect(url_for('main.clients'))
    return render_template('client_form.html')

@main_bp.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.email = request.form.get('email')
        client.address = request.form.get('address')
        client.gstin = request.form.get('gstin')
        client.pan = request.form.get('pan')
        db.session.commit()
        flash('Client updated successfully', 'success')
        return redirect(url_for('main.clients'))
    return render_template('client_form.html', client=client)

@main_bp.route('/invoices', methods=['GET'])
def invoices():
    all_invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('invoices.html', invoices=all_invoices)

@main_bp.route('/invoices/new', methods=['GET', 'POST'])
def new_invoice():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        invoice_number = request.form.get('invoice_number')
        issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        tax_type = request.form.get('tax_type')
        notes = request.form.get('notes')
        
        invoice = Invoice(
            client_id=client_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            tax_type=tax_type,
            notes=notes
        )
        db.session.add(invoice)
        db.session.flush() # get invoice ID
        
        # Add items
        descriptions = request.form.getlist('description[]')
        sac_codes = request.form.getlist('sac_code[]')
        amounts = request.form.getlist('amount[]')
        
        for i in range(len(descriptions)):
            if descriptions[i].strip() and amounts[i].strip():
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=descriptions[i],
                    sac_code=sac_codes[i],
                    amount=float(amounts[i])
                )
                db.session.add(item)
                
        db.session.commit()
        flash('Invoice created successfully', 'success')
        return redirect(url_for('main.invoices'))
        
    # Fetch clients from API if connected, otherwise use local DB
    clients = []
    if session.get('api_url') and session.get('api_key'):
        try:
            resp = requests.get(session['api_url'], params={'api_key': session['api_key']}, timeout=5)
            if resp.status_code == 200:
                clients = resp.json().get('clients', [])
        except Exception as e:
            flash(f"Could not connect to Manage App: {str(e)}", 'warning')
            clients = [{'id': c.id, 'name': c.name, 'gstin': c.gstin} for c in Client.query.all()]
    else:
        clients = [{'id': c.id, 'name': c.name, 'gstin': c.gstin} for c in Client.query.all()]
        
    setting = Settings.query.first()
    # Generate next invoice number
    last_inv = Invoice.query.order_by(Invoice.id.desc()).first()
    next_num = f"INV-{datetime.now().strftime('%Y%m')}-{(last_inv.id + 1 if last_inv else 1):03d}"
    
    return render_template('invoice_form.html', clients=clients, setting=setting, next_num=next_num, today=datetime.now().strftime('%Y-%m-%d'))

@main_bp.route('/invoices/<int:id>')
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    setting = Settings.query.first()
    return render_template('invoice_view.html', invoice=invoice, setting=setting)

@main_bp.route('/invoices/<int:id>/print')
def print_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    setting = Settings.query.first()
    return render_template('invoice_print.html', invoice=invoice, setting=setting)
