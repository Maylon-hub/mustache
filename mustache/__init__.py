import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Configuration - allow override via environment variable for production security
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-mustache-change-in-prod')
    
    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)
    
    return app
