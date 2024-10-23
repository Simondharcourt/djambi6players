


Djambi game with personal rules at 6 players, to develop a reinforcement learing strategy.

For now, it plays randomly.

Runs on python3.10.13 with a single script board.py.

## How to use locally:
I used python3.10.13. (for ex, use miniconda, and install an env with 3.10.13)
Then install pango and cairo ('brew install cairo pango' on macos/apt-get install 'cairo pango')
Then, in your virtual environment, install the requirements (you just need pygame, cairosvg, gym and tensorflow)
('pip install -r requirements.txt', or with environment.yml)
Then: python board.py

## How to play it online with your friends:
Same environment.
Then: python server.py
Then, to continue.

## Todo:
Plenty of things to do. On 3 parts: online part, ia part and game part.

- online: 
Implement possibility to play online. The server will rely on server.py and board.py but should implement the possible movements.
Start with the possibility to host only one game (with 6 navigators on the website).
If works well, will add possibility to host several games, add an account and elo ranking.
Not the objective for now, just to play it with friends.

- ai part.
train the model on a platform.

- game part.
small stuff: kill a chief by surronding, end game if a chief is sourrounded in the middle.
implement 2 and 3 players game
improve playability
fix some bugs.