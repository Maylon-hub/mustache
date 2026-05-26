from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev'
    
    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)
    
    return app
