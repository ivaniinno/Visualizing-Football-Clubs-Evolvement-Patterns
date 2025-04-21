import json

with open("natonal_kader.json", "r", encoding="utf-8") as f:
    national_teams = json.load(f)

with open("all_kader.json", "r", encoding="utf-8") as f:
    club_teams = json.load(f)

national_players_by_year = {}
for entry in national_teams:
    year = entry["Year"]
    if year not in national_players_by_year:
        national_players_by_year[year] = set()
    national_players_by_year[year].update(entry["PlayerIDS"])

for club in club_teams:
    year = club["Year"]
    if year in national_players_by_year:
        club_national_players = set(club["PlayerIDS"]) & national_players_by_year[year]
        club["NationalPlayersCount"] = len(club_national_players)
    else:
        club["NationalPlayersCount"] = 0

with open("updated_club_teams.json", "w", encoding="utf-8") as f:
    json.dump(club_teams, f, ensure_ascii=False, indent=4)