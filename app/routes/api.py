from flask import Blueprint, jsonify, request
from db import get_conn

api_bp = Blueprint('api', __name__, url_prefix='/api')


def build_query(base_sql, allowed_filters, allowed_sorts, allowed_null_fields):
    """
    Builds a parameterized SQL query from HTTP request arguments.
    Supports sorting, pagination (limit/offset), NULL filtering

    Args:
        base_sql:         Base SQL query to wrap
        allowed_filters:  List of permitted filter columns
        allowed_sorts:    List of allowed sorting columns
        allowed_null_fields: Fields allowed for NULL handling
    
    Returns:
        tuple: (sql_query, query_params, error_message, http_status)
               Returns (None, None, error, status) on validation failure
    """
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
          SELECT * FROM ({base_sql}) AS subquery
          {f'WHERE {where_clause}' if where_clause else ''}
          ORDER BY {sort_by} {order}
          {f'LIMIT {limit}' if limit else ''}
          {f'OFFSET {offset}' if offset else ''}
    """
    
    return sql, params, None, None


def handle_get_request(base_sql, allowed_filters, allowed_sorts, allowed_null_fields):
    """
    Executes a parameterized SQL query for GET requests and returns JSON results.
    
    Args:
        base_sql: Base SQL query to extend
        allowed_filters: List of allowed sorting columns
        allowed_sorts: List of allowed sorting columns
        allowed_null_fields: Fields allowed for NULL handling
    
    Returns:
        JSON response with data (camelCase keys) or error message
    """
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
            mapped_data = map_keys_to_camel(data)
        return jsonify(mapped_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and not conn.closed:
            conn.close()


# Mapping of snake_case database keys to camelCase JSON response keys.
# Used in map_keys_to_camel()
key_mapping = {
    'national_team_id': 'NationalTeamID',
    'year': 'Year',
    'team_cost': 'TeamCost',
    'total_legionnaires_amount': 'TotalLegionnairesAmount',
    'num_of_national_players': 'NationalPlayersCount',
    'average_age_among_clubs': 'AverageAgeAmongClubs',
    'average_points': 'AveragePoints',
    'team_id': 'TeamID',
    'transfer_balance': 'TransferBalance',
    'average_age': 'AverageAge',
    'team_size_ratio': 'TeamSizeRatio',
    'club_ids': 'ClubIDs',
    'national_team_name': 'NationalTeamName',
    'image_link': 'ImageLink',
    'number_of_cups': 'NumberOfCups',
    'team_name': 'TeamName',
    'number_of_titles_this_year': 'NumberOfTitlesThisYear',
    'players_in_national_team': 'PlayersInNationalTeam',
    'total_country_cost': 'TotalCountryCost',
    'legioners': 'Legioners',
    'national_players_count': 'NationalPlayersCount'
}



def map_keys_to_camel(data):
    """
    Converts snake_case database keys to camelCase for API responses.
    
    Args:
        data: List of database rows (as dicts) with snake_case keys
        
    Returns:
        List of dicts with camelCase keys according to key_mapping.
    """
    return [{key_mapping.get(k, k): v for k, v in row.items()} for row in data]


@api_bp.route('/full_players_costs', methods=['GET'])
def get_full_players_costs():
    """
    Get national teams players costs
    ---
    tags:
      - Statistics
    summary: Get aggregated players costs by national teams
    description: Returns total players costs grouped by national teams and years
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: year
        in: query
        type: integer
        description: Filter by statistic year
      - name: total_country_cost
        in: query
        type: number
        format: float
        description: Filter by total cost value
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, year, total_country_cost]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sort direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, year, total_country_cost]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Results offset for pagination
    responses:
      200:
        examples:
          application/json:
            - NationalTeamID: 3262
              TotalCountryCost: 4468520
              Year: 2018
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            n.national_team_id,
            tys.year,
            SUM(tys.team_cost) AS total_country_cost
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        JOIN national_teams n ON t.national_team_id = n.national_team_id
        GROUP BY n.national_team_id, tys.year
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'total_country_cost'],
        allowed_sorts=['national_team_id', 'year', 'total_country_cost'],
        allowed_null_fields=['national_team_id', 'year', 'total_country_cost']
    )


@api_bp.route('/average_team_cost', methods=['GET'])
def get_average_team_cost():
    """
    Get average team costs
    ---
    tags:
      - Statistics
    summary: Calculate average team costs per national team
    description: Returns average costs aggregated by national teams and years
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: year
        in: query
        type: integer
        description: Filter by statistic year
      - name: team_cost
        in: query
        type: number
        format: float
        description: Filter by average cost value
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, year, team_cost]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, year, team_cost]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum number of results
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - NationalTeamID: 3262
              TeamCost: 279282
              Year: 2018
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
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


@api_bp.route('/legionnaires_total_amount', methods=['GET'])
def get_legionnaires_total_amount():
    """
    Get legionnaires statistics
    ---
    tags:
      - Statistics
    summary: Get total legionnaires amount by national teams
    description: Returns aggregated legionnaires count per national team and year
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: year
        in: query
        type: integer
        description: Filter by statistic year
      - name: total_legionnaires_amount
        in: query
        type: integer
        description: Filter by total legionnaires count
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, year, total_legionnaires_amount]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting order
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, year, total_legionnaires_amount]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - NationalTeamID: 3262
              TotalLegionnairesAmount: 364
              Year: 2018
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
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


@api_bp.route('/total_average_age' ,methods=['GET'])
def get_total_average_age():
    """
    Get average clubs age statistics
    ---
    tags:
      - Statistics
    summary: Calculate average clubs age per national team
    description: Returns aggregated average age of clubs by national teams and years
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: year
        in: query
        type: integer
        description: Filter by statistic year
      - name: average_age_among_clubs
        in: query
        type: number
        format: float
        description: Filter by average age value
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, year, average_age_among_clubs]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, year, average_age_among_clubs]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum number of results
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - AverageAgeAmongClubs: 25.2750000000000000
              NationalTeamID: 3262
              Year: 2018
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
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


@api_bp.route('/average_points_per_team', methods=['GET'])
def get_average_points_per_team():
    """
    Get average points per team
    ---
    tags:
      - Statistics
    summary: Get average points per team
    description: Returns average points statistics per team and year
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
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, average_points]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum number of results
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - AveragePoints: 1.24
              TeamID: 3
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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


@api_bp.route('/club_titles', methods=['GET'])
def get_club_titles():
    """
    Get club titles statistics
    ---
    tags:
      - Statistics
    summary: Get club titles by years
    description: Returns number of titles per team and year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: number_of_titles_this_year
        in: query
        type: integer
        description: Filter by titles count
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, number_of_titles_this_year]
        default: team_id
        description: Sorting field
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, number_of_titles_this_year]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Results limit
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - NumberOfTitlesThisYear: 0
              TeamID: 3
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            team_id,
            year,
            number_of_titles_this_year
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'number_of_titles_this_year'],
        allowed_sorts=['team_id', 'year', 'number_of_titles_this_year'],
        allowed_null_fields=['team_id', 'year', 'number_of_titles_this_year']
    )


@api_bp.route('/clubs_and_national_players', methods=['GET'])
def get_clubs_and_national_players():
    """
    Get national team players in clubs
    ---
    tags:
      - Statistics
    summary: Get club-national team players relations
    description: Returns number of club players participating in national teams
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: players_in_national_team
        in: query
        type: integer
        description: Filter by national team players count
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, players_in_national_team]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, players_in_national_team]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - PlayersInNationalTeam: 9
              Year: 2018
              TeamID: 3
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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
    Get total team costs
    ---
    tags:
      - Statistics
    summary: Get team financial statistics
    description: Returns total team costs per year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: team_cost
        in: query
        type: number
        format: float
        description: Filter by total cost value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, team_cost]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, team_cost]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - TeamCost: 50750
              TeamID: 3
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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


@api_bp.route('/transfer_balance', methods=['GET'])
def get_transfer_balance():
    """
    Get team transfer balance
    ---
    tags:
      - Statistics
    summary: Get team transfer balance data
    description: Returns financial balance from transfers per team and year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: transfer_balance
        in: query
        type: number
        format: float
        description: Filter by transfer balance value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, transfer_balance]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, transfer_balance]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - TeamID: 3
              TransferBalance: -8300
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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


@api_bp.route('/legionnaires_per_team', methods=['GET'])
def get_legionnaires_per_team():
    """
    Get team legionnaires count
    ---
    tags:
      - Statistics
    summary: Get legionnaires count per team
    description: Returns number of legionnaires per team and year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: legioners
        in: query
        type: integer
        description: Filter by legionnaires count
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, legioners]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, legioners]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - Legioners: 22
              TeamID: 3
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            team_id,
            year,
            legionnaires AS legioners
        FROM team_yearly_stats
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'year', 'legioners'],
        allowed_sorts=['team_id', 'year', 'legioners'],
        allowed_null_fields=['team_id', 'year', 'legioners']
    )


@api_bp.route('/average_age_per_team', methods=['GET'])
def get_average_age_per_team():
    """
    Get team average age
    ---
    tags:
      - Statistics
    summary: Get average age statistics per team
    description: Returns average age data for teams by year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
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
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, average_age]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - AverageAge: 25.8
              TeamID: 3
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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
    Get team size ratio statistics
    ---
    tags:
      - Statistics
    summary: Get team size ratio data
    description: Returns team size ratio statistics per team and year
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: year
        in: query
        type: integer
        description: Filter by season year
      - name: team_size_ratio
        in: query
        type: number
        format: float
        description: Filter by size ratio value
      - name: sort_by
        in: query
        type: string
        enum: [team_id, year, team_size_ratio]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, year, team_size_ratio]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - TeamID: 3
              TeamSizeRatio: null
              Year: 2014
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
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


@api_bp.route('/club_info', methods=['GET'])
def get_club_info():
    """
    Get club information
    ---
    tags:
      - Statistics
    summary: Get basic club information
    description: Returns club details including cups count and national team affiliation
    parameters:
      - name: team_id
        in: query
        type: integer
        description: Filter by team ID
      - name: team_name
        in: query
        type: string
        description: Filter by team name
      - name: number_of_cups
        in: query
        type: integer
        description: Filter by number of cups won
      - name: national_team_id
        in: query
        type: integer
        description: Filter by associated national team ID
      - name: image_link
        in: query
        type: string
        description: Filter by image URL
      - name: sort_by
        in: query
        type: string
        enum: [team_id, team_name, number_of_cups, national_team_id, image_link]
        default: team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [team_id, team_name, number_of_cups, national_team_id, image_link]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - ImageLink: https://tmssl.akamaized.net//images/wappen/head/3.png?lm=1656580823
              NationalTeamID: 3262
              NumberOfCups: 13
              TeamID: 3
              TeamName: Кёльн
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            team_id,
            team_name,
            number_of_cups,
            national_team_id,
            image_link
        FROM teams
    """
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['team_id', 'team_name', 'number_of_cups', 'national_team_id', 'image_link'],
        allowed_sorts=['team_id', 'team_name', 'number_of_cups', 'national_team_id', 'image_link'],
        allowed_null_fields=['team_id', 'team_name', 'number_of_cups', 'national_team_id', 'image_link']
    )


@api_bp.route('/country_info', methods=['GET'])
def get_country_info():
    """
    Get country information
    ---
    tags:
      - Statistics
    summary: Get national teams with associated clubs
    description: Returns national team data with aggregated club IDs
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: national_team_name
        in: query
        type: string
        description: Filter by national team name
      - name: club_ids
        in: query
        type: array
        items:
          type: integer
        collectionFormat: multi
        description: Filter by associated club IDs
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, national_team_name, club_ids]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, national_team_name, club_ids]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - ClubIDs: [3, 15, 16, 18, 24, 27, 33, 39, 44, 60, 79, 82, 89, 533, 2036, 23826]
              NationalTeamID: 3262
              NationalTeamName: Германия
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            nt.national_team_id,
            nt.national_team_name,
            ARRAY_AGG(t.team_id) AS "club_ids"
        FROM national_teams nt
        LEFT JOIN teams t ON nt.national_team_id = t.national_team_id
        GROUP BY nt.national_team_id, nt.national_team_name
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'national_team_name', 'club_ids'],
        allowed_sorts=['national_team_id', 'national_team_name', 'club_ids'],
        allowed_null_fields=['national_team_id', 'national_team_name', 'club_ids'],
    )


@api_bp.route('/national_teams_players_total_amount', methods=['GET'])
def get_national_teams_players_total_amount():
    """
    Get national teams players total
    ---
    tags:
      - Statistics
    summary: Get total national team players count
    description: Returns aggregated number of national team players by country and year
    parameters:
      - name: national_team_id
        in: query
        type: integer
        description: Filter by national team ID
      - name: year
        in: query
        type: integer
        description: Filter by statistic year
      - name: national_players_count
        in: query
        type: integer
        description: Filter by total players count
      - name: sort_by
        in: query
        type: string
        enum: [national_team_id, year, national_players_count]
        default: national_team_id
        description: Field to sort results
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: asc
        description: Sorting direction
      - name: exclude_nulls
        in: query
        type: boolean
        default: false
        description: Exclude records with null values
      - name: exclude_null_fields
        in: query
        type: string
        enum: [national_team_id, year, national_players_count]
        collectionFormat: multi
        description: Specific fields to exclude nulls for
      - name: limit
        in: query
        type: integer
        description: Maximum results to return
      - name: offset
        in: query
        type: integer
        description: Pagination offset
    responses:
      200:
        examples:
          application/json:
            - NationalPlayersCount: 145
              NationalTeamID: 3262
              Year: 2018
      400:
        description: Invalid request parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid fields for null exclusion: ['invalid_field']"
      500:
        description: Internal server error
    """
    base_query = """
        SELECT 
            t.national_team_id,
            tys.year,
            SUM(tys.players_in_national_team) AS national_players_count
        FROM teams t
        JOIN team_yearly_stats tys ON t.team_id = tys.team_id
        WHERE t.national_team_id IS NOT NULL
        GROUP BY t.national_team_id, tys.year
    """
    
    return handle_get_request(
        base_sql=base_query,
        allowed_filters=['national_team_id', 'year', 'national_players_count'],
        allowed_sorts=['national_team_id', 'year', 'national_players_count'],
        allowed_null_fields=['national_team_id', 'year', 'national_players_count']
    )
