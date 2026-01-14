from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/lhl_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_TOKEN_LOCATION'] = ['headers']

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# Import and register blueprints (must be after db is initialized)
# Using function to avoid circular imports
def register_blueprints():
    from api import auth, simulations, teams, stats, admin
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(simulations.bp, url_prefix='/api/simulations')
    app.register_blueprint(teams.bp, url_prefix='/api/teams')
    app.register_blueprint(stats.bp, url_prefix='/api/stats')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')

register_blueprints()

@app.route('/api/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
