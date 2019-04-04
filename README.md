# py-goratschin
An UCI "chess engine" that combines the power of Lc0 and Stockfish - or any two other engines, you like.

The code borrows heavily from the project [CombiChess](https://github.com/tom0334/CombiChess).
Many Thanks to Tom Friederich for his work!

GoratschinChess a "chess engine" that supports the UCI chess protocol and combines 2 engines (called 'boss' and 'clerk', respectively) into one. It works by asking the engines what they think the best move is for a given position, and then applying some logic to determine what move to actually do.

The rules that it uses are fairly simple:

  * If an engine sees a mate, then do that move leading to mate immediately.

  * If both engines give the same best move, then do that move.
  
  * if the engines say something else, and the score of the clerk is better than that of the boss by a margin 'cp' (see self.score_margin in code) do the clerk's move. The default margin is 0.5 centipawns.
  
  * Else, always listen to the 'boss engine'. 
  
'Goratschin' is the name of a double-headed figure from the german sci-fi series "Perry Rhodan".
  

## Using GoratschinChess
To use GoratschinChess, clone the project or download it as a zip. Unzip it if needed, and then place the engines you want to use in the engines folder. Open GoratschinLauncher.py and change the filenames to the ones in the engines folder you want to use.

GoratschinChess has one dependency: python-chess. Assuming you have python on your computer, you can install it by opening a terminal and typing the following:

```
pip install python-chess
```

To run GoratschinChess as a python program, execute the GoratschinLauncher.py, NOT the GoratschinChess.py!

On Windows, you may run Goratschin.bat for conveniance. This can also be used as the engine command in Arena, CuteChess, etc.
