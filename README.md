


Djambi game with personal rules at 6 players, to develop a reinforcement learing strategy. You can play it online.

See here: https://fr.wikipedia.org/wiki/Djambi the original game.

You can find my adapted rules in the repository.


## How to use locally:
Runs on python3.10.13 with backend/src/main.py
You need to install pango and cairo ('brew install cairo pango' on macos/apt-get install 'cairo pango')

Specify --nb_player_mode (3, 4 or 6. Default is 6)

## How to play it online with your friends:
Just with https://simondharcourt.github.io/djambi6players/.
To test it locally, with python backend/src/server.py and click on the html file.

## Code structure
- backend: python backend hosted on heroku
- frontend: frontend hosted on github pages
- local: to run the board locally and train it.
- rules: a latex doc with the rules. Could be simplified.

## Todo:
Plenty of things to do. On 3 parts: online part, ia part and game part.

#### - online:
Make it mobile friendly. Add an ios app?
Add 4 player mode?
Add an elo ?
Maybe later, add possibility to host several games.
Find the remaning bugs and fix them.

#### - ai part.
2 parts: minimax and rl.
-- minimax part: it is actually a maxn algorithm, not a minmax, as it is a 6 players game. There is a lot of challenges about it, on complexity, as the depth should be at least to be pertinent. A pre-sort of the action should be made to filter all possible moves. 
-- rl part: train the model on a platform. Get inspired by trainings on chess. Many possibilities to define the state space and the action space.

#### - game part.
the player should get all zombies by going acceding in the middle. Easy but not prioritary.
