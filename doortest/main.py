"""
Main Application Entry Point for Door Face Panels
Initializes Flask app and runs the smart door security system
"""
import logging
import os
from flask import Flask, render_template
from api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and run Flask application"""
    # Create app with template folder
    app = create_app('config')
    
    # Configure template and static folders
    app.template_folder = os.path.join(os.path.dirname(__file__), 'dashboard', 'templates')
    app.static_folder = os.path.join(os.path.dirname(__file__), 'dashboard', 'static')
    
    # Serve dashboard
    @app.route('/')
    def dashboard():
        """Serve main dashboard"""
        return render_template('index.html')
    
    logger.info("=" * 60)
    logger.info("Door Face Panels - Smart Door Security System")
    logger.info("=" * 60)
    logger.info("Facial Recognition + Anomaly Detection + Threat Detection")
    logger.info("For Elderly Care and Safety Monitoring")
    logger.info("=" * 60)
    
    # Run app
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Dashboard available at http://localhost:{port}/")
    logger.info(f"API docs available at http://localhost:{port}/api")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
