import json


with open("updated_club_teams.json", "r", encoding="utf-8") as file:
    clubs = json.load(file)

clubs.sort(key=lambda x: (x["TeamID "].strip(), x["Year"]))

for i in range(len(clubs)):
    if i > 0 and clubs[i]["TeamID "] == clubs[i - 1]["TeamID "]:
        current_size = clubs[i]["TeamSize"]
        previous_size = clubs[i - 1]["TeamSize"]
        clubs[i]["TeamSizeRatio"] = round(current_size / previous_size, 2) if previous_size != 0 else None
    else:
        clubs[i]["TeamSizeRatio"] = None


with open("complete_clubs.json", "w", encoding="utf-8") as file:
    json.dump(clubs, file, ensure_ascii=False, indent=4)