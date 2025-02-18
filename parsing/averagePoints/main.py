import json

with open("average_points.json", 'r', encoding='utf-8') as avg_file:
    average_points = json.load(avg_file)

with open("sorted_teams.json", 'r', encoding='utf-8') as teams_file:
    teams = json.load(teams_file)


all_years = set(range(2014, 2025))


team_years_map = {}
for entry in average_points:
    team_id = entry["TeamID"]
    year = entry["Year"]
    if team_id not in team_years_map:
        team_years_map[team_id] = set()
    team_years_map[team_id].add(year)

result = []
for team in teams:
    team_id = team["TeamID"]
    recorded_years = team_years_map.get(team_id, set())
    left_years = sorted(list(all_years - recorded_years))
    if len(left_years) != 0:
        result.append({
            "TeamID": team_id,
            "LeftYears": left_years
        })

with open("missing_years.json", 'w', encoding='utf-8') as outfile:
    json.dump(result, outfile, ensure_ascii=False, indent=4)
