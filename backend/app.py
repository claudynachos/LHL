from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/lhl_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
# Set JWT token expiration to 7 days (604800 seconds) for long draft sessions
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 604800  # 7 days in seconds

# Initialize extensions with app
from extensions import db, jwt
db.init_app(app)
jwt.init_app(app)

# JWT error handlers for debugging
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print(f"JWT INVALID: {error_string}")
    return jsonify({'error': f'Invalid token: {error_string}'}), 422

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    print(f"JWT UNAUTHORIZED: {error_string}")
    return jsonify({'error': f'Missing token: {error_string}'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"JWT EXPIRED")
    return jsonify({'error': 'Token has expired'}), 401

cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
cors_origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]

# Configure CORS to handle preflight requests automatically
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": cors_origins_list,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type"]
        }
    },
    supports_credentials=True
)

# Ensure all models are registered before handling requests
with app.app_context():
    from models import user, simulation, team, game, player, trophy  # noqa: F401

# Import and register blueprints
def register_blueprints():
    from api import auth, simulations, teams, stats, admin, players, trophies
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(simulations.bp, url_prefix='/api/simulations')
    app.register_blueprint(teams.bp, url_prefix='/api/teams')
    app.register_blueprint(stats.bp, url_prefix='/api/stats')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    app.register_blueprint(players.bp, url_prefix='/api/players')
    app.register_blueprint(trophies.bp, url_prefix='/api/trophies')

register_blueprints()

@app.route('/api/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
