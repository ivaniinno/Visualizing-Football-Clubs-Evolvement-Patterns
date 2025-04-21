from flask import Flask
from routes.api import api_bp
from flasgger import Swagger

# Main Flask application
app = Flask(__name__)

# Register API routes blueprint
app.register_blueprint(api_bp)

# Initialize automatic Swagger documentation at /apidocs
swagger = Swagger(app)
