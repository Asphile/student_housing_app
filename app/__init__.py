"""
DUT Student Housing & Roommate Matching System - Application Factory
File: app/__init__.py
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
import os

# 1. Initialize extensions globally (Empty objects)
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()

# Login Management Security Settings
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    """
    Application Factory: Creates and configures the Flask instance.
    """
    try:
        app = Flask(__name__)
        
        # Enable logging
        import logging
        logging.basicConfig(level=logging.INFO)
        app.logger.info("Starting DUT Housing App...")
        
        # 2. CORE SYSTEM CONFIGURATION
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_2026_student_housing_portal')
        
        # Database configuration - use environment variable or fallback to SQLite
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.logger.info("Using DATABASE_URL from environment")
        else:
            # For Render, use a persistent SQLite location in /tmp
            if os.environ.get('RENDER'):
                db_path = '/tmp/housing_app.db'
                # Ensure /tmp exists and is writable
                try:
                    os.makedirs('/tmp', exist_ok=True)
                    # Test write access
                    with open('/tmp/test_write', 'w') as f:
                        f.write('test')
                    os.remove('/tmp/test_write')
                    app.logger.info("/tmp directory is writable")
                except Exception as e:
                    app.logger.error(f"/tmp directory not writable: {e}")
                    db_path = 'housing_app.db'  # fallback to current directory
            else:
                db_path = os.path.join(os.path.dirname(app.instance_path), 'site.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            app.logger.info(f"Using SQLite database at: {db_path}")
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # 3. GMAIL EMAIL CONFIGURATION
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
        
        # Credentials
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'asphilelubanyana@gmail.com')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'gzwlwgfnpoxqtmod')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', ('DUT Student Housing', 'asphilelubanyana@gmail.com'))

        # 4. BINDING EXTENSIONS TO APP INSTANCE
        # This "attaches" the global objects to this specific app
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        bcrypt.init_app(app)
        mail.init_app(app)

        # 5. BLUEPRINT REGISTRATION (Inside the factory to avoid Circular Imports)
        from app.routes.auth import auth as auth_blueprint
        from app.routes.main import main as main_blueprint

        app.register_blueprint(auth_blueprint)
        app.register_blueprint(main_blueprint)

        # 6. DATABASE MODELS & USER SESSION LOADER
        with app.app_context():
            from app.models.user import User

            @login_manager.user_loader
            def load_user(user_id):
                try:
                    return User.query.get(int(user_id))
                except Exception as e:
                    app.logger.error(f"Error loading user {user_id}: {e}")
                    return None
            
            # Create all database tables
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.error(f"Database initialization error: {e}")
                # Log the full traceback for debugging
                import traceback
                app.logger.error(f"Full traceback: {traceback.format_exc()}")
                # Don't fail app startup on DB errors - let it try to run

        app.logger.info("Flask app created successfully")
        return app
        
    except Exception as e:
        # Critical error during app creation
        import logging
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.error(f"CRITICAL ERROR during app creation: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Re-raise the exception to fail the deployment
        raise

# Create app instance for production (Render/Gunicorn)
app = create_app()