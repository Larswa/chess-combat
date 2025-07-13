import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'detailed_console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        'app': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn.access': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

def setup_logging(debug=False):
    """Setup logging configuration"""
    if debug:
        # Use detailed logging for debug mode
        LOGGING_CONFIG['handlers']['console'] = LOGGING_CONFIG['handlers']['detailed_console']
        LOGGING_CONFIG['root']['level'] = 'DEBUG'
        LOGGING_CONFIG['loggers']['app']['level'] = 'DEBUG'

    logging.config.dictConfig(LOGGING_CONFIG)
