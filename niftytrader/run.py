#!/usr/bin/env python
"""
NiftyTrader - Advanced Nifty Market Analysis Dashboard
Application Entry Point
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from niftytrader import create_app, socketio

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))


if __name__ == '__main__':
    """Run the application"""
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', app.debug)
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║         NiftyTrader - Market Analysis Dashboard      ║
    ║              Starting Application...                 ║
    ╠══════════════════════════════════════════════════════╣
    ║ Server: http://{host}:{port}
    ║ Environment: {os.environ.get('FLASK_ENV', 'development')}
    ║ Debug Mode: {debug}
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Run with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug,
        log_output=True
    )
