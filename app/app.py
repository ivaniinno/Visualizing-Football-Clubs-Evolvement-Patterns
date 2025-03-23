from flask import Flask, render_template, send_from_directory, make_response
from routes.api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp)

csp = (
        f"default-src *;"
        f"script-src 'self'"
    )

@app.after_request
def apply_csp_headers(resp):
    resp.headers['Content-Security-Policy'] = csp
    return resp


@app.route('/')
def index():
    return make_response(render_template('index.html'))
