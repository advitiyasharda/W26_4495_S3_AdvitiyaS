"""
API Module for Door Face Panels Smart Security System
"""
from flask import Flask
from flask_cors import CORS

def create_app(config_name='config'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_name)
    
    # Enable CORS — allow requests from the Next.js dev server and production build
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # Initialize database before registering routes
    from data.database import Database
    app.db = Database()
    
    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
