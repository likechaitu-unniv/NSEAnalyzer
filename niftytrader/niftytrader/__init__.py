"""
NiftyTrader - Advanced Nifty Market Analysis Dashboard
Flask Application Factory
"""

from flask import Flask
from flask_socketio import SocketIO
from config import get_config
import os

# Initialize SocketIO
socketio = SocketIO()


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment ('development', 'production', or 'testing')
    
    Returns:
        Configured Flask application instance
    """
    
    # Determine base paths
    basedir = os.path.dirname(os.path.abspath(__file__))
    
    # Create Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static'),
        static_url_path='/static'
    )
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register CLI commands
    _register_cli_commands(app)
    
    return app


def _register_blueprints(app):
    """Register all blueprints"""
    from niftytrader.routes.main import main_bp
    from niftytrader.routes.dashboard import dashboard_bp
    from niftytrader.routes.trends import trends_bp
    from niftytrader.routes.guide import guide_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(trends_bp)
    app.register_blueprint(guide_bp)


def _register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template, jsonify, request
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not Found', 'status': 404}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template, jsonify, request
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal Server Error', 'status': 500}), 500
        return render_template('errors/500.html'), 500


def _register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_data():
        """Initialize application data"""
        print("Initializing application data...")
        # Add initialization logic here
        print("Data initialized successfully!")


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
