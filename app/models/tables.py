from dataclasses import dataclass

@dataclass
class AveragePointsPerTeam:
    id: int
    team_id: int
    team_name: str
    average_points: float

    def to_dict(self):
        return {
            'teamId': self.team_id,
            'team_name': self.team_name,
            'average_points': self.average_points
        }

@dataclass
class AverageAgePerTeam:
    team_id: int
    year: int
    average_age: float

    def to_dict(self):
        return {
            'teamId': self.team_id,
            'year': self.year,
            'average_age': self.average_age
        }

@dataclass
class ClubsAndNationalPlayers:
    year: int
    team_id: int
    players_in_national_team: int

    def to_dict(self):
        return {
            'teamId': self.team_id,
            'year': self.year,
            'players_in_national_team': self.players_in_national_team
        }

@dataclass
class LegionnairesPerTeam:
    team_id: int
    year: int
    legioners: int

    def to_dict(self):
        return {
            'teamId': self.team_id,
            'year': self.year,
            'legioners': self.legioners
        }