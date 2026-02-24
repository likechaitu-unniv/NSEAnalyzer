"""
Configuration settings for NiftyTrader application
"""

import os
from datetime import datetime

# Get the base directory
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'niftytrader-dev-key-2026'
    JSON_SORT_KEYS = False
    
    # SocketIO settings
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_ASYNC_MODE = "threading"
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False
    
    # API settings
    NSE_API_TIMEOUT = 10
    DEFAULT_EXPIRY = '24-Feb-2026'
    
    # Data storage
    DATA_DIR = os.path.join(BASEDIR, 'niftytrader', 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Application info
    APP_NAME = 'NiftyTrader'
    APP_VERSION = '1.0.0'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SOCKETIO_LOGGER = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SOCKETIO_LOGGER = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration object based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config_dict.get(env, config_dict['default'])
