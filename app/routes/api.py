from flask import Blueprint, jsonify

from db import conn, cur

api_bp = Blueprint('api', __name__, url_prefix='/api')
