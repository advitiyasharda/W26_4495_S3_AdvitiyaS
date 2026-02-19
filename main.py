"""
Main Application Entry Point for Door Face Panels
Runs the Flask API server (frontend is served separately by Next.js on port 3000)
"""
import logging
import os
from api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and run Flask API application"""
    app = create_app('config')

    logger.info("=" * 60)
    logger.info("Door Face Panels - Smart Door Security System")
    logger.info("=" * 60)
    logger.info("Facial Recognition + Anomaly Detection + Threat Detection")
    logger.info("For Elderly Care and Safety Monitoring")
    logger.info("=" * 60)

    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    logger.info(f"Flask API running on http://{host}:{port}")
    logger.info("Frontend (Next.js) should run separately on http://localhost:3000")
    logger.info("=" * 60)

    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
