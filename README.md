


Djambi game with personal rules at 6 players, to develop a reinforcement learing strategy.

For now, it plays randomly.


## How to use locally:
Runs on python3.10.13 with a single script board.py.
You need to install pango and cairo ('brew install cairo pango' on macos/apt-get install 'cairo pango')

## How to play it online with your friends:
Just with https://simondharcourt.github.io/djambi6players/.
To test locally, with python server.py and click on the html file.

## Code structure
- backend: python backend hosted on heroku
- frontend: frontend hosted on github pages
- local: to run the board locally
- rules: a latex doc with the rules

## Todo:
Plenty of things to do. On 3 parts: online part, ia part and game part.

- online:
Add undo/redo buttons.
Maybe later, add possibility to host several games, add an account and elo ranking.

- ai part.
train the model on a platform. Get inspired by trainings on chess.
On the side, add a minmax algorithm to still be able to play alone (to suggest one players game online)

- game part.
get zombies by going acceding in the middle.
