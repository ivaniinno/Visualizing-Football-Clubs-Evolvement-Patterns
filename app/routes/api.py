from flask import Blueprint, jsonify, request
from db import get_conn

api_bp = Blueprint('api', __name__, url_prefix='/api')


def build_query(base_sql, allowed_filters, allowed_sorts, allowed_null_fields=None):
    filters = []
    params = []
    for key in allowed_filters:
        value = request.args.get(key)
        if value is not None:
            filters.append(f"{key} = %s")
            params.append(value)

    sort_by = request.args.get('sort_by', default=allowed_sorts[0])
    order = request.args.get('order', default='asc').upper()
    if sort_by not in allowed_sorts or order not in ['ASC', 'DESC']:
        return None, None, "Invalid sort parameters", 400

    null_conditions = []
    exclude_nulls = request.args.get('exclude_nulls', 'false').lower() == 'true'
    exclude_null_fields = request.args.getlist('exclude_null_fields')

    if allowed_null_fields:
        invalid_fields = [f for f in exclude_null_fields if f not in allowed_null_fields]
        if invalid_fields:
            return None, None, f"Invalid fields for null exclusion: {invalid_fields}", 400

        for field in exclude_null_fields:
            null_conditions.append(f"{field} IS NOT NULL")

        if exclude_nulls:
            for field in allowed_null_fields:
                if field not in exclude_null_fields:
                    null_conditions.append(f"{field} IS NOT NULL")

    all_conditions = filters + null_conditions
    where_clause = " AND ".join(all_conditions) if all_conditions else ""

    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)

    sql = f"""
        {base_sql}
        {f'WHERE {where_clause}' if where_clause else ''}
        ORDER BY {sort_by} {order}
        {f'LIMIT {limit}' if limit else ''}
        {f'OFFSET {offset}' if offset else ''}
    """
    
    return sql, params, None, None


def handle_get_request(base_sql, allowed_filters, allowed_sorts, allowed_null_fields):
    sql, params, error, status = build_query(
        base_sql=base_sql,
        allowed_filters=allowed_filters,
        allowed_sorts=allowed_sorts,
        allowed_null_fields=allowed_null_fields
    )
    
    if error:
        return jsonify({"error": error}), status
    
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            data = cur.fetchall()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and not conn.closed:
            conn.close()


@api_bp.route('/average_points', methods=['GET'])
def get_average_points():
    base_query = """
        SELECT 
            team_id,
            year,
            average_points
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'average_points'],
        allowed_sorts=['team_id', 'year', 'average_points'],
        allowed_null_fields=['team_id', 'year', 'average_points']
    )


@api_bp.route('/team_names', methods=['GET'])
def get_titles():
    base_query = """
        SELECT 
            team_id,
            team_name
        FROM teams
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'team_name'],
        allowed_sorts=['team_id', 'team_name'],
        allowed_null_fields=['team_id', 'team_name']
    )


@api_bp.route('/national_team_players', methods=['GET'])
def get_national_team_players():
    base_query = """
        SELECT 
            team_id,
            year,
            players_in_national_team
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'players_in_national_team'],
        allowed_sorts=['team_id', 'year', 'players_in_national_team'],
        allowed_null_fields=['team_id', 'year', 'players_in_national_team']
    )


@api_bp.route('/total_team_cost', methods=['GET'])
def get_total_team_cost():
    base_query = """
        SELECT 
            team_id,
            year,
            team_cost
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'team_cost'],
        allowed_sorts=['team_id', 'year', 'team_cost'],
        allowed_null_fields=['team_id', 'year', 'team_cost']
    )


@api_bp.route('/cup_winnings', methods=['GET'])
def get_cup_winnings():
    base_query = """
        SELECT 
            team_id,
            number_of_cups
        FROM teams
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'number_of_cups'],
        allowed_sorts=['team_id', 'number_of_cups'],
        allowed_null_fields=['team_id', 'number_of_cups']
    )


@api_bp.route('/transfer_balance', methods=['GET'])
def get_transfer_balance():
    base_query = """
        SELECT 
            team_id,
            year,
            transfer_balance
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'transfer_balance'],
        allowed_sorts=['team_id', 'year', 'transfer_balance'],
        allowed_null_fields=['team_id', 'year', 'transfer_balance']
    )


@api_bp.route('/number_of_legionnaires', methods=['GET'])
def get_number_of_legionnaires():
    base_query = """
        SELECT 
            team_id,
            year,
            legionnaires
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'legionnaires'],
        allowed_sorts=['team_id', 'year', 'legionnaires'],
        allowed_null_fields=['team_id', 'year', 'legionnaires']
    )


@api_bp.route('/average_age', methods=['GET'])
def get_average_age():
    base_query = """
        SELECT 
            team_id,
            year,
            average_age
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'average_age'],
        allowed_sorts=['team_id', 'year', 'average_age'],
        allowed_null_fields=['team_id', 'year', 'average_age']
    )


@api_bp.route('/team_size_ratio', methods=['GET'])
def get_team_size_ratio():
    base_query = """
        SELECT 
            team_id,
            year,
            team_size_ratio
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'team_size_ratio'],
        allowed_sorts=['team_id', 'year', 'team_size_ratio'],
        allowed_null_fields=['team_id', 'year', 'team_size_ratio']
    )


@api_bp.route('/teams_info', methods=['GET'])
def get_teams_info():
    base_query = """
        SELECT 
            team_id,
            team_name,
            image_link,
            national_team_id
        FROM teams
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'team_name', 'image_link', 'national_team_id'],
        allowed_sorts=['team_id', 'team_name', 'image_link', 'national_team_id'],
        allowed_null_fields=['team_id', 'team_name', 'image_link', 'national_team_id']
    )


@api_bp.route('/countries_info', methods=['GET'])
def get_countries_info():
    base_query = """
        SELECT 
            nt.national_team_id,
            nt.national_team_name,
            ARRAY_AGG(t.team_id) AS "team_ids"
        FROM national_teams nt
        LEFT JOIN teams t ON nt.national_team_id = t.national_team_id
        GROUP BY nt.national_team_id, nt.national_team_name
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'national_team_name', 'team_ids'],
        allowed_sorts=['national_team_id', 'national_team_name', 'team_ids'],
        allowed_null_fields=['national_team_id', 'national_team_name', 'team_ids']
    )
