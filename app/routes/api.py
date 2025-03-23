from flask import Blueprint, jsonify

from models import conn, cur
from models.tables import *

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/average_points_per_team', methods=['GET'])
def get_average_points_per_team():
    try:
        cur.execute('SELECT * FROM average_points_per_team')
        average_points_per_team = [
            AveragePointsPerTeam(id=row[0], team_id=row[1], team_name=row[2], average_points=row[3])
            for row in cur.fetchall()
        ]
        return jsonify([element.to_dict() for element in average_points_per_team]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/average_age_per_team', methods=['GET'])
def get_average_age_per_team():
    try:
        cur.execute('SELECT * FROM average_age_per_team')
        average_age_per_team = [
            AverageAgePerTeam(team_id=row[0], year=row[1], average_age=row[2])
            for row in cur.fetchall()
        ]
        return jsonify([element.to_dict() for element in average_age_per_team]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/clubs_and_national_players', methods=['GET'])
def get_clubs_and_national_players():
    try:
        cur.execute('SELECT * FROM clubs_and_national_players')
        clubs_and_national_players = [
            ClubsAndNationalPlayers(team_id=row[0], year=row[1], players_in_national_team=row[2])
            for row in cur.fetchall()
        ]
        return jsonify([element.to_dict() for element in clubs_and_national_players]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/legionnaires_per_team', methods=['GET'])
def get_legionnaires_per_team():
    try:
        cur.execute('SELECT * FROM legionnaires_per_team')
        legionnaires_per_team = [
            LegionnairesPerTeam(team_id=row[0], year=row[1], legioners=row[2])
            for row in cur.fetchall()
        ]
        return jsonify([element.to_dict() for element in legionnaires_per_team]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
