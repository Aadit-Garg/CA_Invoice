from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-for-ca-invoice'
    
    # Use SQLite for easy local setup, can be changed to postgres via env
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'invoice.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from app.models import Client, Invoice, InvoiceItem, Settings
        db.create_all()

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
