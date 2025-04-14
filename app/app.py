from flask import Flask
from routes.api import api_bp
from flasgger import Swagger

app = Flask(__name__)
app.register_blueprint(api_bp)
swagger = Swagger(app)
