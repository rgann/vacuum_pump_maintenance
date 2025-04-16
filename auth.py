"""
Authentication module for the Vacuum Pump Maintenance application
"""
import os
import json
import logging
import sys
from flask import Flask, redirect, url_for, session, request, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
import requests
from datetime import datetime, timedelta
from functools import wraps

# Setup logging
logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()

def setup_auth(app):
    """Setup authentication for the application"""
    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Configure Google OAuth
    google = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID', ''),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'token_endpoint_auth_method': 'client_secret_post'
        },
        api_base_url='https://www.googleapis.com/oauth2/v3/',
    )

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        # Check if user exists in session
        if 'users' not in session:
            return None

        users = session['users']
        if user_id in users:
            return User(
                id=users[user_id]['id'],
                email=users[user_id]['email'],
                name=users[user_id]['name'],
                picture=users[user_id].get('picture', '')
            )
        return None

    # Add login route
    @app.route('/login')
    def login():
        # Log login attempt
        logger.info("Login attempt initiated")

        try:
            # Get the redirect URI
            redirect_uri = url_for('authorize', _external=True)
            logger.info(f"Redirect URI: {redirect_uri}")

            # Log OAuth client configuration
            client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
            logger.info(f"Using client ID: {client_id[:5]}...{client_id[-5:] if client_id else ''}")

            # Redirect to Google OAuth
            return oauth.google.authorize_redirect(redirect_uri)
        except Exception as e:
            logger.error(f"Error in login route: {str(e)}", exc_info=True)
            flash(f"Login configuration error: {str(e)}", "danger")
            return redirect(url_for('index'))

    # Add logout route
    @app.route('/logout')
    def logout():
        logout_user()
        session.pop('users', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # Add authorization callback route
    @app.route('/authorize')
    def authorize():
        try:
            # Log the request for debugging
            logger.info(f"Authorization request received. Query params: {request.args}")

            # Get token from Google
            token_data = oauth.google.authorize_access_token()
            logger.info(f"Successfully obtained access token: {token_data.get('token_type', 'unknown')} token")

            # Get user info from Google
            logger.info("Attempting to get user info from Google")
            resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
            user_info = resp.json()
            logger.info(f"Retrieved user info for: {user_info.get('email', 'unknown')}")

            # More detailed logging for debugging
            logger.info(f"Full user info: {user_info}")

            # Check if user email is allowed
            user_email = user_info.get('email', '')
            if not is_allowed_email(user_email):
                logger.warning(f"Unauthorized access attempt from email: {user_email}")
                flash('Your email is not authorized to access this application.', 'danger')
                return redirect(url_for('index'))

            logger.info(f"User {user_email} authorized successfully")

            # Create user object
            user = User(
                id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture', '')
            )

            # Store user in session
            if 'users' not in session:
                session['users'] = {}

            session['users'][user.id] = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'picture': user.picture
            }

            # Log in user
            login_user(user)
            logger.info(f"User {user_email} logged in successfully")

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')

            flash(f'Welcome, {user.name}!', 'success')
            return redirect(next_page)

        except Exception as e:
            logger.error(f"Detailed error during authorization: {str(e)}", exc_info=True)
            flash(f'Login error: {str(e)}', 'danger')
            return redirect(url_for('index'))

    # Add admin required decorator
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))

            if not is_admin_email(current_user.email):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)
        return decorated_function

    # Add debug route for OAuth configuration
    @app.route('/oauth-debug')
    def oauth_debug():
        """Debug endpoint to check OAuth configuration"""
        try:
            # Get client configuration
            client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

            # Get OAuth client metadata
            metadata = None
            try:
                metadata = oauth.google.load_server_metadata()
            except Exception as e:
                metadata = {"error": str(e)}

            config = {
                'client_id_set': bool(client_id),
                'client_id_preview': f"{client_id[:5]}...{client_id[-5:]}" if client_id else None,
                'client_secret_set': bool(client_secret),
                'redirect_uri': url_for('authorize', _external=True),
                'allowed_domains': os.environ.get('ALLOWED_EMAIL_DOMAINS', '').split(','),
                'admin_emails': os.environ.get('ADMIN_EMAILS', '').split(','),
                'server_metadata': metadata,
                'flask_env': os.environ.get('FLASK_ENV', 'development'),
                'request_url': request.url,
                'base_url': request.url_root
            }
            return jsonify(config)
        except Exception as e:
            return jsonify({
                'error': str(e),
                'traceback': str(sys.exc_info())
            })

    # Add auth routes to app context
    app.login = login
    app.logout = logout
    app.authorize = authorize
    app.admin_required = admin_required
    app.oauth_debug = oauth_debug

    # Initialize OAuth with app
    oauth.init_app(app)

    return login_manager

def is_allowed_email(email):
    """Check if email is allowed to access the application"""
    if not email:
        logger.warning("Empty email provided to is_allowed_email")
        return False

    # Get allowed domains from environment variable
    allowed_domains_str = os.environ.get('ALLOWED_EMAIL_DOMAINS', '')
    logger.info(f"Allowed domains configuration: {allowed_domains_str}")

    allowed_domains = allowed_domains_str.split(',')
    allowed_domains = [d.strip().lower() for d in allowed_domains if d.strip()]

    # If no domains are specified, allow all emails
    if not allowed_domains:
        logger.info("No allowed domains specified, allowing all emails")
        return True

    # Check if email domain is in allowed domains
    try:
        email_domain = email.split('@')[-1].lower()
        is_allowed = email_domain in allowed_domains

        if is_allowed:
            logger.info(f"Email domain {email_domain} is allowed")
        else:
            logger.warning(f"Email domain {email_domain} is not in allowed domains: {allowed_domains}")

        return is_allowed
    except Exception as e:
        logger.error(f"Error checking email domain: {e}")
        return False

def is_admin_email(email):
    """Check if email is an admin email"""
    # Get admin emails from environment variable
    admin_emails = os.environ.get('ADMIN_EMAILS', '').split(',')
    admin_emails = [e.strip().lower() for e in admin_emails if e.strip()]

    # If no admin emails are specified, no one is admin
    if not admin_emails:
        return False

    # Check if email is in admin emails
    return email.lower() in admin_emails

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, email, name, picture=''):
        self.id = id
        self.email = email
        self.name = name
        self.picture = picture
