"""
API Module for Door Face Panels Smart Security System
"""
from flask import Flask
from flask_cors import CORS

def create_app(config_name='config'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_name)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
