from flask import Flask, render_template, send_from_directory, make_response

app = Flask(__name__)

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


@app.route('/data')
def get_data():
    return send_from_directory('data', 'dataset.json')


if __name__ == '__main__':
    app.run(debug=True)