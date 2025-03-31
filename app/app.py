from flask import Flask, render_template, send_from_directory, make_response
from routes.api import api_bp
from flasgger import Swagger

app = Flask(__name__)
app.register_blueprint(api_bp)
swagger = Swagger(app)

csp = (
    "default-src 'self';"
    "script-src 'self' https://cdn.jsdelivr.net;"
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline';"
    "img-src 'self' data: https://*.swagger.io;"
)

# @app.after_request
# def apply_csp_headers(resp):
#     resp.headers['Content-Security-Policy'] = csp
#     return resp


@app.route('/')
def index():
    return make_response(render_template('index.html'))
