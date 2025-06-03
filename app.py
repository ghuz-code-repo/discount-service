from flask import Flask, url_for
from models import db, User
from routes import init_app
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from pathlib import Path
import os
from prefix_middleware import PrefixMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Check if running behind proxy
behind_proxy = os.getenv('BEHIND_PROXY', 'false').lower() == 'true'
prefix = '/discount-system' if behind_proxy else ''
print(f"Using URL prefix: '{prefix}'")

# Initialize Flask app
app = Flask(__name__, 
           static_url_path='/static',  # Simple static path, we'll adjust it if needed
           static_folder='static')

# Configure app to work behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Direct route handler for static files with the prefix
@app.route('/discount-system/static/<path:filename>')
def custom_static(filename):
    print(f"Custom static file request for: {filename}")
    return app.send_static_file(filename)

# Configure app
app.config.update(
    SERVER_NAME=None,  # Set to None to avoid URL generation issues
    SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('SECRET_KEY', 'default-secret-key'),
    APPLICATION_ROOT=prefix,
    PREFERRED_URL_SCHEME='http',
    MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB max upload size
)

# Initialize database
db.init_app(app)

# Apply PrefixMiddleware if running behind proxy
if behind_proxy:
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, app=app, prefix=prefix)
    print(f"Applied PrefixMiddleware with prefix: {prefix}")
    
    # Test URL generation to debug
    with app.test_request_context():
        print(f"Test static URL: {url_for('static', filename='css/common.css')}")

# Register all blueprints
init_app(app)

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
    # Run the application
    app.run(host='0.0.0.0', port=80, debug=True)