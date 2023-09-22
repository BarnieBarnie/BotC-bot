from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATABASE_DIR = SCRIPT_DIR / 'databases'
DATABASE_DIR.mkdir(exist_ok=True)

DOCUMENTATION_STRING_1 = """
1/2
Descriptions of commands

/spectate
Links you to another player. Everytime they move to another voice channel you move to that channel aswell. Used to spectate a Storyteller to learn the Storyteller role.

/stop_spectate
Unlinks you from the player you were spectating, you no longer follow them around.

/game
Start a new game. This command gives you the buttons to control the game with. The buttons only respond to you, they are bound to you not other player can use them.
You need the Storyteller role to be able to link a day and night category to your game. Use /st for that.
When calling this command you need to specify a day category, a night category and the town_square voice channel. This is needed to link these to your game, so multiple games can run at the same time.

The game controls have the following buttons:
- Day - Moves all players except you from the night channels to the town_square channel
- Night - Moves all players except you from the town_square channel to the night channels, each player to their own channel.
- Cancel timer - Cancels the timer if one was set, see more about timers below
- Quit game - Quits the game and removes the Storyteller role from you
- Select time players have until vote - Select how many minutes the timer should take. If the timer reaches 0 all players from the day channels are moved to the Town Square channel. This is used to give players a certain time to talk before voting starts. This also updates the #game-chat channel every 30 seconds so players know how much time they have left.

/stop_game
Stop the game. You should always try to stop the game with the "Quit game" button. But if for some reason that doesn't work you can stop the game using this command, this does not remove the Storyteller role use /st for that.
"""

DOCUMENTATION_STRING_2 = """
2/2
/create_game_channels
This creates the channels for a game. If you can just use existing channels by linking them to your game with /game. But if multiple games should run next to eachother use this to make channels for your game. Making channels this way is the most reliable way to make sure the bot has all the permissions to manage your game properly.

/delete_game_channels
This deletes the game channels specified by you. This will only delete channels made by this bot. It will throw an error if you try to delete non bot made categories and it won't delete anything then.

/clean_channel
This deletes all messages from a text channel. This is meant for clearing the #game-chat channel. This will only clear channels made by the bot, it will throw an error and not delete anything when trying to clear a non bot created channel.

/st
This gives you the Storyteller role. This allows you to see the night channels and join them. This is also needed before trying to run /game since if you have no Storyteller role you won't be able to link the night category to your game.

/help
This returns all of this information and deletes it after 3 minutes to not fill your entire screen.

"""

DOCUMENTATION_STRINGS = [DOCUMENTATION_STRING_1, DOCUMENTATION_STRING_2]

ROOMS = [
	"Aerary",
	"Air shower",
	"Aircraft cabin",
	"Airport lounge",
	"Aisle",
	"Almonry",
	"Anechoic chamber",
	"Apodyterium",
	"Arizona room",
	"Assembly hall",
	"Atrium",
	"Attic",
	"Auditorium",
	"Aula regia",
	"Ballroom",
	"Bang",
	"Banishment room",
	"Bank vault",
	"Banking hall",
	"Banquet hall",
	"Basement",
	"Bathroom",
	"Battery room",
	"Bedroom",
	"Billiard room",
	"Bonus room",
	"Boudoir",
	"Breezeway",
	"Buttery",
	"Cabinet",
	"Cafeteria",
	"Caldarium",
	"Calefactory",
	"Castle chapel",
	"Central apparatus room",
	"Changing room",
	"Church hall",
	"Church porch",
	"Classroom",
	"Cleanroom",
	"Cloakroom",
	"Closet",
	"Committee room",
	"Common room",
	"Companionway",
	"Computer lab",
	"Conference hall",
	"Conservatory",
	"Control room",
	"Conversation pit",
	"Corner office",
	"Count room",
	"Counting house",
	"Courtroom",
	"Cry room",
	"Crypt",
	"Cryptoporticus",
	"Cubiculum",
	"Cyzicene hall",
	"Darbazi",
	"Dark room",
	"Darkroom",
	"Data room",
	"Den",
	"Dewaniya",
	"Dining room",
	"Diwan-khane",
	"Drawing room",
	"Drying room",
	"Dungeon",
	"Electrical room",
	"Equatorial room",
	"Equipment room",
	"Execution chamber",
	"Fainting room",
	"Family room",
	"First aid room",
	"Frigidarium",
	"Function hall",
	"Furnace room",
	"Garden office",
	"Garderobe",
	"Garret",
	"Genkan",
	"Ghorfa",
	"Granary",
	"Great chamber",
	"Great hall",
	"Great room",
	"Green room",
	"Hall",
	"Hallway",
	"Harem",
	"Hidden compartment",
	"Honeymoon suite",
	"Inglenook",
	"Kitchen",
	"Laconicum",
	"Lactation room",
	"Lanai",
	"Larder",
	"Laundry room",
	"Living room",
	"Lobby",
	"Locker room",
	"Loft",
	"Long gallery",
	"Lumber room",
	"Luxury box",
	"Maashaus",
	"Mail services center",
	"Mailroom",
	"Majlis",
	"Man cave",
	"Master control",
	"Mechanical floor",
	"Mechanical room",
	"Megaron",
	"Mehmaan khana",
	"Mission control center",
	"Mizuya",
	"Monastic cell",
	"Money room",
	"Musalla",
	"Music rehearsal space",
	"Network operations center",
	"Nilavara",
	"Nursery",
	"Oecus",
	"Office",
	"Opisthodomos",
	"Padded cell",
	"Pantry",
	"Parlour",
	"Period room",
	"Pinacotheca",
	"Portego",
	"Porters' lodge",
	"Porticus",
	"Presidential suite",
	"Priest hole",
	"Print room",
	"Prison cell",
	"Psychomanteum",
	"Public toilet",
	"Qa'a",
	"Quiet room",
	"Railway refreshment room",
	"Rain porch",
	"Recreation room",
	"Refectory",
	"Reredorter",
	"Riding hall",
	"Room number",
	"Roomsharing",
	"Root cellar",
	"Rotunda",
	"Sacristy",
	"Safe room",
	"Sauna",
	"Screened porch",
	"Secret passage",
	"Semi-basement",
	"Sensitive compartmented information facility",
	"Servants' hall",
	"Servants' quarters",
	"Server room",
	"Shoin",
	"Showroom",
	"Sky lobby",
	"Skyway",
	"Sleeping porch",
	"Slick (hiding place)",
	"Slype",
	"Small office/home office",
	"Smoking room",
	"Solar",
	"Staffroom",
	"Staircase tower",
	"State room",
	"Still room",
	"Storage room",
	"Storm cellar",
	"Stube",
	"Student lounge",
	"Studio",
	"Study",
	"Sudatorium",
	"Suite",
	"Sunroom",
	"Tabagie",
	"Tablinum",
	"Tasting room",
	"Tepidarium",
	"Throne room",
	"Torture chamber",
	"Transmission control room",
	"Triclinium",
	"Undercroft",
	"Utility room",
	"Utility vault",
	"Vestibule",
	"Waiting room",
	"Walk-in closet",
	"Washitsu",
	"Whispering gallery",
	"Wine cellar",
	"Wiring closet"
]
ROOMS_COUNT = len(ROOMS)

TIMERS = {}