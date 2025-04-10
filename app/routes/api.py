from flask import Blueprint, jsonify, request
from db import get_conn

api_bp = Blueprint('api', __name__, url_prefix='/api')


def build_query(base_sql, allowed_filters, allowed_sorts, allowed_null_fields):
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

    print(sql)
    
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
            mapped_data = map_keys_to_camel(data)
        return jsonify(mapped_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and not conn.closed:
            conn.close()


key_mapping = {
    'national_team_id': 'NationalTeamID',
    'year': 'Year',
    'team_cost': 'TeamCost',
    # 'average_team_cost': 'TeamCost',
    # 'num_of_legionnaires': 'TotalLegionnairesAmount',
    'total_legionnaires_amount': 'TotalLegionnairesAmount',
    'num_of_national_players': 'NationalPlayersCount',
    'average_age_among_clubs': 'AverageAgeAmongClubs',
    'average_points': 'AveragePoints',
    'team_id': 'TeamID',
    'transfer_balance': 'TransferBalance',
    'average_age': 'AverageAge',
    'team_size_ratio': 'TeamSizeRatio',
    # 'team_ids': 'ClubIDs',
    'club_ids': 'ClubIDs',
    'national_team_name': 'NationalTeamName',
    'image_link': 'ImageLink',
    'number_of_cups': 'NumberOfCups',
    'team_name': 'TeamName',
    'number_of_titles_this_year': 'NumberOfTitlesThisYear',
    'players_in_national_team': 'PlayersInNationalTeam',
    'total_country_cost': 'TotalCountryCost',
    # 'legionnaires': 'Legioners',
    'legioners': 'Legioners',
    'national_players_count': 'NationalPlayersCount'

}


def map_keys_to_camel(data):
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
        description: Successfully retrieved costs data
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  year:
                    type: integer
                  total_country_cost:
                    type: number
                    format: float
            example:
              - national_team_id: 10
                year: 2023
                total_country_cost: 1250000.50
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid fields for null exclusion: ['invalid_field']"}
      500:
        description: Internal server error
        content:
          application/json:
            example: {"error": "Failed to calculate costs"}
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
        description: Successfully retrieved average costs
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  year:
                    type: integer
                  team_cost:
                    type: number
                    format: float
            example:
              - national_team_id: 7
                year: 2023
                team_cost: 250000.75
      400:
        description: Invalid parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Cost calculation failed"}
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
        description: Successfully retrieved legionnaires data
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  year:
                    type: integer
                  total_legionnaires_amount:
                    type: integer
            example:
              - national_team_id: 5
                year: 2023
                total_legionnaires_amount: 15
      400:
        description: Invalid request
        content:
          application/json:
            example: {"error": "Invalid legionnaires filter parameters"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch legionnaires data"}
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
        description: Successfully retrieved age data
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  year:
                    type: integer
                  average_age_among_clubs:
                    type: number
                    format: float
            example:
              - national_team_id: 8
                year: 2023
                average_age_among_clubs: 26.4
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Age calculation failed"}
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
        description: Successfully retrieved points data
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
              - team_id: 12
                year: 2023
                average_points: 18.7
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch points data"}
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
        description: Successfully retrieved titles data
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
                  number_of_titles_this_year:
                    type: integer
            example:
              - team_id: 7
                year: 2023
                number_of_titles_this_year: 2
      400:
        description: Invalid parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch titles data"}
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
        description: Successfully retrieved national players data
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
            example:
              - team_id: 5
                year: 2023
                players_in_national_team: 8
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch national players data"}
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
        description: Successfully retrieved cost data
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
            example:
              - team_id: 15
                year: 2023
                team_cost: 1500000.50
      400:
        description: Invalid parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch cost data"}
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
        description: Successfully retrieved transfer data
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
            example:
              - team_id: 10
                year: 2023
                transfer_balance: 500000.75
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch transfer data"}
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
        description: Successfully retrieved legionnaires data
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
                  legioners:
                    type: integer
            example:
              - team_id: 3
                year: 2023
                legioners: 5
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch legionnaires data"}
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
        description: Successfully retrieved age data
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
            example:
              - team_id: 10
                year: 2023
                average_age: 26.5
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch age data"}
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
        description: Successfully retrieved size ratio data
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
            example:
              - team_id: 5
                year: 2023
                team_size_ratio: 1.2
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch size ratio data"}
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
        description: Successfully retrieved club data
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
                  number_of_cups:
                    type: integer
                  national_team_id:
                    type: integer
                  image_link:
                    type: string
            example:
              - team_id: 1
                team_name: "FC Champions"
                number_of_cups: 5
                national_team_id: 10
                image_link: "https://example.com/team1.jpg"
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to retrieve club information"}
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
        description: Successfully retrieved country data
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
                  club_ids:
                    type: array
                    items:
                      type: integer
            example:
              - national_team_id: 1
                national_team_name: "National Team A"
                club_ids: [101, 102, 103]
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to retrieve country data"}
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
        description: Successfully retrieved players count data
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  national_team_id:
                    type: integer
                  year:
                    type: integer
                  national_players_count:
                    type: integer
            example:
              - national_team_id: 5
                year: 2023
                national_players_count: 45
      400:
        description: Invalid request parameters
        content:
          application/json:
            example: {"error": "Invalid null exclusion field: 'invalid_field'"}
      500:
        description: Server error
        content:
          application/json:
            example: {"error": "Failed to fetch players count data"}
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
