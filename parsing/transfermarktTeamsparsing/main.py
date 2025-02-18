import json

with open('national_teams.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

seen = set()
cleaned_data = []

for item in data:
    if item['NationalTeamID'] not in seen:
        cleaned_data.append(item)
        seen.add(item['NationalTeamID'])

with open('national_teams.json', 'w', encoding='utf-8') as file:
    json.dump(cleaned_data, file, ensure_ascii=False, indent=4)

print("Duplicates removed and cleaned data saved.")



def sort_teams_by_page(input_file: str, output_file: str):
    with open(input_file, 'r', encoding='utf-8') as f:
        teams = json.load(f)
    sorted_teams = sorted(teams, key=lambda x: x.get('Page', 0))
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_teams, f, ensure_ascii=False, indent=4)

    print(f"Data sorted and saved to {output_file}")


input_json = 'transfermarktTeamsparsing/national_teams.json'
output_json = 'transfermarktTeamsparsing/sorted_national_teams.json'
sort_teams_by_page(input_json, output_json)