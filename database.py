from global_vars import DATABASE_DIR
import json

class Database:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.filename = self.owner.strip(' ')
        self.path = DATABASE_DIR / f'{self.filename}.json'
        self.game_name = f"{self.owner}'s game"
        self.view_id = None
        self.linked_objects = False
        self.players: dict = {}
        self.day_category = {}
        self.night_category = {}
        self.town_square = []

    def to_dict(self):
        return {
            "owner": self.owner,
            "game_name": self.game_name,
            "view_id": self.view_id,
            "players": self.players,
            "day_category": self.day_category,
            "night_category": self.night_category,
            "town_square": self.town_square
        }
    
    def save_to_file(self):
        with open(self.path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def find_town_square(self):
        for channel in self.day_category['children']:
            if channel[0] == 'Town Square (main game)':
                self.town_square = channel
                return