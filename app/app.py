from os import urandom
from flask import Flask, render_template, send_from_directory, make_response

app = Flask(__name__)

@app.route('/')
def index():
    nonce = urandom(16).hex()
    
    csp = (
        f"default-src 'self';"
        f"style-src 'self' 'unsafe-inline';"
        f"script-src 'self' 'nonce-{nonce}';"
        f"connect-src 'self';"
    )
    
    response = make_response(render_template('index.html', nonce=nonce))
    response.headers['Content-Security-Policy'] = csp
    return response


@app.route('/data')
def get_data():
    return send_from_directory('data', 'dataset.json')


if __name__ == '__main__':
    app.run(debug=True)