from flask import Blueprint, jsonify, request
from db import get_conn
from flask_restx import Namespace, resource, fields

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


@api_bp.route('/full_players_cost', methods=['GET'])
def get_full_players_cost():
    base_query = """
        SELECT 
            n.national_team_id,
            tys.year,
            SUM(tys.team_cost)
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        JOIN national_teams n ON t.national_team_id = n.national_team_id
        GROUP BY n.national_team_id, tys.year
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'team_cost'],
        allowed_sorts=['national_team_id', 'year', 'team_cost'],
        allowed_null_fields=['national_team_id', 'year', 'team_cost']
    )


@api_bp.route('/average_team_cost', methods=['GET'])
def get_average_team_cost():
    base_query = """
        SELECT 
            n.national_team_id,
            tys.year,
            SUM(tys.team_cost) / COUNT(t.team_id) AS team_cost
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        JOIN national_teams n ON t.national_team_id = n.national_team_id
        GROUP BY n.national_team_id, tys.year
    """

    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'team_cost'],
        allowed_sorts=['national_team_id', 'year', 'team_cost'],
        allowed_null_fields=['national_team_id', 'year', 'team_cost']
    )


@api_bp.route('/num_of_legionnaires', methods=['GET'])
def get_num_of_legionnaires():
    base_query =    """
        SELECT 
            n.national_team_id,
            tys.year,
            SUM(tys.legionnaires) AS total_legionnaires_amount
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        JOIN national_teams n ON t.national_team_id = n.national_team_id
        GROUP BY n.national_team_id, tys.year
    """

    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'total_legionnaires_amount'],
        allowed_sorts=['national_team_id', 'year', 'total_legionnaires_amount'],
        allowed_null_fields=['national_team_id', 'year', 'total_legionnaires_amount']
    )

@api_bp.route('/num_of_national_players' ,methods=['GET'])
def get_num_of_national_players():
    base_query =    """
        SELECT 
            team_id,
            year,
            SUM(players_in_national_team) AS num_of_national_players
        FROM team_yearly_stats
        GROUP BY team_id, year
    """

    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'num_of_national_players'],
        allowed_sorts=['team_id', 'year', 'num_of_national_players'],
        allowed_null_fields=['team_id', 'year', 'num_of_national_players']
    )


@api_bp.route('/total_average_age' ,methods=['GET'])
def get_total_average_age():
    base_query =    """
        SELECT 
            n.national_team_id,
            tys.year,
            SUM(tys.average_age) / COUNT(tys.average_age) AS average_age_among_clubs
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        JOIN national_teams n ON t.national_team_id = n.national_team_id
        GROUP BY n.national_team_id, tys.year
    """

    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'average_age_among_clubs'],
        allowed_sorts=['national_team_id', 'year', 'average_age_among_clubs'],
        allowed_null_fields=['national_team_id', 'year', 'average_age_among_clubs']
    )


@api_bp.route('/average_points', methods=['GET'])
def get_average_points():
    """
    Get average team points statistics
    ---
    tags:
      - Statistics
    summary: Get average points by teams over years
    description: Returns average points data
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: average_points
        in: query
        type: number
        format: float
        description: Filter by average points value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, average_points]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, average_points]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  average_points:
                    type: number
                    format: float
            example:
              - team_id: 1
                year: 2023
                average_points: 85.5
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team names
    ---
    tags:
      - Statistics
    summary: Get team names
    description: Returns team titles
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: team_name
        in: query
        type: string
        description: Filter by team name
      - name: sort_by
        in: query
        type: string
        enum: [team_id, team_name]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, team_name]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  team_name:
                    type: string
                required:
                  - team_id
                  - team_name
            example:
              - team_id: 1
                team_name: "Dream Team"
              - team_id: 2
                team_name: "Champions"
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get national team players statistics
    ---
    tags:
      - Statistics
    summary: Get data about players in national teams
    description: Returns data about players participating in national teams
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: players_in_national_team
        in: query
        type: integer
        description: Filter by number of players in national team
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, players_in_national_team]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, players_in_national_team]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  players_in_national_team:
                    type: integer
                required:
                  - team_id
                  - year
                  - players_in_national_team
            example:
              - team_id: 1
                year: 2022
                players_in_national_team: 5
              - team_id: 1
                year: 2023
                players_in_national_team: 7
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team financial statistics
    ---
    tags:
      - Statistics
    summary: Get data about team costs
    description: Returns data with total team cost
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: team_cost
        in: query
        type: number
        format: float
        description: Filter by team total cost value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, team_cost]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, team_cost]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  team_cost:
                    type: number
                    format: float
                required:
                  - team_id
                  - year
                  - team_cost
            example:
              - team_id: 1
                year: 2023
                team_cost: 1500000.50
              - team_id: 2
                year: 2022
                team_cost: 1350000.00
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team cup achievements
    ---
    tags:
      - Statistics
    summary: Get team cup winnings
    description: Returns data about team cup winnings
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: number_of_cups
        in: query
        type: integer
        description: Filter by number of cups won
      - name: sort_by
        in: query
        type: string
        enum: [team_id, number_of_cups]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, number_of_cups]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  number_of_cups:
                    type: integer
                required:
                  - team_id
                  - number_of_cups
            example:
              - team_id: 1
                number_of_cups: 5
              - team_id: 2
                number_of_cups: 3
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team transfer balance statistics
    ---
    tags:
      - Statistics
    summary: Get transfer balance data
    description: Returns transfer balance data
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: transfer_balance
        in: query
        type: number
        format: float
        description: Filter by transfer balance value (income - expenses)
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, transfer_balance]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, transfer_balance]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  transfer_balance:
                    type: number
                    format: float
                required:
                  - team_id
                  - year
                  - transfer_balance
            example:
              - team_id: 1
                year: 2023
                transfer_balance: 2500000.75
              - team_id: 2
                year: 2022
                transfer_balance: -500000.00
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team international players statistics
    ---
    tags:
      - Statistics
    summary: Get data about foreign players
    description: Returns data about number of international players in teams
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: legionnaires
        in: query
        type: integer
        description: Filter by number of foreign players
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, legionnaires]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, legionnaires]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  legionnaires:
                    type: integer
                required:
                  - team_id
                  - year
                  - legionnaires
            example:
              - team_id: 1
                year: 2023
                legionnaires: 8
              - team_id: 2
                year: 2022
                legionnaires: 5
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team age statistics
    ---
    tags:
      - Statistics
    summary: Get historical data about average team age
    description: Returns data about average age of players in teams
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: average_age
        in: query
        type: number
        format: float
        description: Filter by average age value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, average_age]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, average_age]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  average_age:
                    type: number
                    format: float
                required:
                  - team_id
                  - year
                  - average_age
            example:
              - team_id: 1
                year: 2023
                average_age: 25.3
              - team_id: 2
                year: 2022
                average_age: 27.1
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get team size dynamics
    ---
    tags:
      - Statistics
    summary: Get historical team size ratio data
    description: Returns data about team size ratio changes
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: team_size_ratio
        in: query
        type: number
        format: float
        description: Filter by team size ratio value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, team_size_ratio]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, team_size_ratio]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  year:
                    type: integer
                  team_size_ratio:
                    type: number
                    format: float
                required:
                  - team_id
                  - year
                  - team_size_ratio
            example:
              - team_id: 1
                year: 2023
                team_size_ratio: 1.25
              - team_id: 2
                year: 2022
                team_size_ratio: 0.95
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get extended team information
    ---
    tags:
      - Statistics
    summary: Get detailed team profiles
    description: Returns data with team metadata and national team associations
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: team_name
        in: query
        type: string
        description: Filter by team name
      - name: image_link
        in: query
        type: string
        description: Filter by image URL
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team association ID
      - name: sort_by
        in: query
        type: string
        enum: [team_id, team_name, image_link, national_team_id]
        default: team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, team_name, image_link, national_team_id]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  team_id:
                    type: integer
                  team_name:
                    type: string
                  image_link:
                    type: string
                  national_team_id:
                    type: integer
                    nullable: true
                required:
                  - team_id
                  - team_name
                  - image_link
                  - national_team_id
            example:
              - team_id: 1
                team_name: "Dream Team"
                image_link: "https://example.com/team1.jpg"
                national_team_id: 101
              - team_id: 2
                team_name: "Champions United"
                image_link: "https://example.com/team2.png"
                national_team_id: null
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
    """
    Get national teams with associated clubs
    ---
    tags:
      - Statistics
    summary: Get national team data with club associations
    description: Returns aggregated data about national teams and their associated clubs
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: national_team_name
        in: query
        type: string
        description: Filter by national team name
      - name: team_ids
        in: query
        type: array
        items:
          type: integer
        collectionFormat: multi
        description: Filter by associated team IDs
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, national_team_name, team_ids]
        default: national_team_id
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude all null values for allowed fields
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, national_team_name, team_ids]
        collectionFormat: multi
        description: Specific fields to exclude null values for
      - name: limit
        in: query
        type: integer
        description: Limit number of results
      - name: offset
        in: query
        type: integer
        description: Results offset
    responses:
      200:
        description: Successful operation
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  national_team_name:
                    type: string
                  team_ids:
                    type: array
                    items:
                      type: integer
                    nullable: true
                required:
                  - national_team_id
                  - national_team_name
                  - team_ids
            example:
              - national_team_id: 101
                national_team_name: "Brazil"
                team_ids: [1, 2, 3]
              - national_team_id: 102
                national_team_name: "Germany"
                team_ids: [4, 5]
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "database connection failed"}
    """
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
