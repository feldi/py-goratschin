import asyncio
import os
import sys
import math
import threading
import subprocess
import time
import logging

import chess.engine

name = "GoratschinChess"
version = "1.2"
fullname = name + '-' + version
author = "P. Feldtmann"

logger = logging.getLogger("goratschinChess")  

# This class contains the inner workings of goratschinChess. If you want to change its settings or start it then
# Please go to goratschinLauncher.py That file also lets you change what engines GoratschinChess uses.
class GoratschinChess:
    # after a stop command, ignore the finish callback. See _checkResult.
    _canceled = False

    # the pythonChess engine objects, loaded from the filePath and fileName
    _engines = [None, None]

    # The current move decided by the engine. None when it doesn't know yet
    _moves = [None, None]
        
    # The current infos
    _info = [None, None]

    _pos = "position startpos"

    # The current score of move decided by the engine. None when it doesn't know yet
    _scores = [None, None]
    _scores_white = [None, None] # from white's view

    # current board status, probably received from UCI position commands
    board = chess.Board()

    # Statistics for how often we listened to each engine, 
    # and how often the engines agreed on a move
    listenedTo = [0, 0]
    agreed = 0

    # Initialized in the init function. These are the folder path and a list of filenames in that folder
    engineFolder = None
    engineFileNames = None
    
    # Margin in centipawns of which the counselor's eval must be better than the boss.
    score_margin = None

    # time control management
    # TODO get factor flexible from parameter?
    tcm_factor = 2 / 3   


    def __init__(self, engineLocation, engineNames, margin):
        self.engineFolder = engineLocation
        self.engineFileNames = engineNames
        self.score_margin = margin / 100 # given in centipawns, default: 50


    def start(self):
        log('Starting ' + fullname)
        emit_and_log(fullname + " by " + author + " based on CombiChess by T. Friederich")
        log('Margin is {:2.2f}'.format(self.score_margin))
        self.init_infos()
        # first start the engines
        for i in range(0, len(self._engines)):
            try:
                engpath = os.path.join(self.engineFolder, self.engineFileNames[i])
                proc = subprocess.Popen(engpath, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
                self._engines[i] = proc

                # start a stdout handler thread for each engine process
                eoh = EngineOutputHandler(proc, i, self)
                eoh.start()

                engineName = self.engineFileNames[i]  
                if i == 0:
                    emit_and_log("info string started engine 0 as boss      (" + engineName + ")")
                else:
                    emit_and_log("info string started engine 1 as counselor (" + engineName + ")")
                
            except Exception as e:
                sys.stderr.write(str(e))
                sys.stderr.write("\nGoratschinChess Error: could not load the engine at file path: " + self.engineFolder + "/" + self.engineFileNames[i])
                sys.stderr.write(
                    "\n\nDid you change the script to include the engines you want to use with GoratschinChess?\n")
                sys.stderr.write("To do this, call GoratschinLauncher.py with argument -e or --enginePath.\n")
                sys.exit()

        # enter the main program loop
        self._mainloop()


    # Main program loop. It keeps waiting for input after a command is finished
    def _mainloop(self):
        exitFlag = False
        while not exitFlag:

            userCommand = input()

            # log("info string cmd: " + userCommand)
            
            if userCommand == "uci":
                emit("id name " + fullname)
                emit("id author " + author)
                self.send_command_to_engines("uci")
                time.sleep(1) #  wait long enough?
                emit("uciok")

            elif userCommand == "ucinewgame":
                self.init_infos()
                self.send_command_to_engines(userCommand)
                log("Starting new game.")

            elif userCommand == "isready":
                self.send_command_to_engines(userCommand)
                emit_and_log("readyok")

            elif userCommand.startswith("setoption"):
                self.send_command_to_engines(userCommand)
                log("Done: " + userCommand)

            elif userCommand.startswith("go"):
                self._canceled = False
                self._moves = [None, None]
                self._scores = [None, None]

                parts = userCommand.split(" ")
                cmds = {}
                for command in ("movetime", "wtime", "btime", "winc", "binc", "depth", "nodes",
                                "movetime", "mate", "movestogo"):
                    if command in parts:
                        cmds[command] = parts[parts.index(command) + 1]

                engineCommand = "go"

                # do a little time control management

                if cmds.get("wtime") is not None:
                    if self.board.turn:  # WHITE to move
                        white_clock = str(int(int(cmds.get("wtime")) * self.tcm_factor))
                        engineCommand += " wtime " + white_clock 
                    else:
                        engineCommand += " wtime " + cmds.get("wtime")

                if cmds.get("btime") is not None:
                    if not(self.board.turn):  # BLACK to move
                         black_clock = str(int(int(cmds.get("btime")) * self.tcm_factor))  
                         engineCommand += " btime " + black_clock 
                    else:
                         engineCommand += " btime " + cmds.get("btime") 

                if cmds.get("winc") is not None:  
                    if self.board.turn:  # WHITE to move
                        white_inc = str(int(int(cmds.get("winc")) * self.tcm_factor))  
                        engineCommand += " winc " + white_inc 
                    else:
                        engineCommand += " winc " + cmds.get("winc") 

                if cmds.get("binc") is not None:
                    if not(self.board.turn):  # BLACK to move
                        black_inc = str(int(int(cmds.get("binc")) * self.tcm_factor))
                        engineCommand += " binc " + black_inc 
                    else:
                        engineCommand += " binc " + cmds.get("binc") 

                if cmds.get("depth") is not None:
                    engineCommand += " depth " + cmds.get("depth") 
                if cmds.get("nodes") is not None:
                   engineCommand += " nodes " + cmds.get("nodes") 
                if cmds.get("movetime") is not None:
                    engineCommand += " movetime " + cmds.get("movetime") 
                if cmds.get("mate") is not None:
                    engineCommand += " mate " + cmds.get("mate") 
                if cmds.get("movestogo") is not None:
                    engineCommand += " movestogo " + cmds.get("movestogo") 
                if parts[1] == "infinite":
                    engineCommand += " infinite " 

                self.send_command_to_engines(engineCommand)
                
                log("Position fen " + self.board.fen())
                log("Started analysis with '" + engineCommand + "'")

            elif userCommand == "stop":
                self.send_command_to_engines("stop")
                emit_and_log("info string stopped analysis")
                
            elif userCommand.startswith("position"):
                self._pos = userCommand
                self._handle_position(userCommand)
                self.send_command_to_engines(userCommand)
                # log("Position " + userCommand)

            elif userCommand == "quit":
                self.send_command_to_engines(userCommand)
                for engine in self._engines:
                    engine.terminate()
                print("Bye.")
                log('Exiting GoratschinChess')
                exitFlag = True
                
            # set multi PV mode
            elif userCommand.startswith("mpv"):  
                parts = userCommand.split(" ")
                mpv_mode = parts[1]
                self.send_command_to_engines("setoption name MultiPV value " + mpv_mode)
                emit_and_log("setting multi pv mode to " + mpv_mode)

            # special tests ...

            # end game study
            elif userCommand.startswith("endg"):  
                self._pos = "position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1 moves e1f2 e8e7"            
                self._handle_position(self._pos)
                self.send_command_to_engines("position fen " + self.board.fen())
                
            # the BDG...
            elif userCommand.startswith("bdg"):   
                self._pos = "position fen rn1qkb1r/ppp1pppp/8/5b2/3Pn3/2N5/PPP3PP/R1BQKBNR w KQkq - 0 6"
                self._handle_position(self._pos)
                self.send_command_to_engines("position fen " + self.board.fen())
                 
            # "My" tabel base setup...
            elif userCommand.startswith("tb"):  
                self.send_command_to_engines("setoption name SyzygyPath value D:/chess/tb-master/tb ")
                    
            # white mates in 3 moves
            elif userCommand.startswith("mw3"): 
                self._pos = "position fen " + "k7/8/8/3K4/8/8/8/7R w - - 4 1" 
                self._handle_position(self._pos)
                self.send_command_to_engines("position fen " + self.board.fen())

             # black mates in 3 moves
            elif userCommand.startswith("mb3"): 
                self._pos = "position fen " + "r7/8/8/8/4k3/8/8/7K b - - 0 1 "
                self._handle_position(self._pos)
                self.send_command_to_engines("position fen " + self.board.fen())

            else:
                emit_and_log("unknown command" + userCommand)

            time.sleep(0.1)


    def send_command_to_engines(self, cmd):
        for engine in self._engines:
           engine.stdin.write(cmd + "\n")
           engine.stdin.flush()


    # Callback handler called from EngineOutputHandler loop
    def _check_result(self, index, info):

        if self._canceled is True:
            return

        # print_and_flush("got info from " +  self.engineFileNames[index] + " >>> " + info)
        if info is None:
            pass

        elif (info.startswith("id ") or
             info.startswith("uciok") or 
             info.startswith("readyok")):
            pass

        elif info.startswith("option"):
            emit(info)

        elif 'currmove' in info:
            pass

        elif 'info depth' in info:
            emit("info string engine " + self.engineFileNames[index] + " says:")
            emit(info)
            # only store main pv
            # since v0.25.x lc0 doesn't emit 'multipv 1' anymore...
            if ('multipv 1' in info) or ('multipv' not in info):
                self._info[index] = info

        elif 'bestmove' in info:
            self._decide(index)       
                   

    # called when 'bestmove' received from any engine               
    def _decide(self, index):

        if self._canceled is True:
            return

        boss = 0
        counselor = 1
        decider = boss
               
        info = self._info[index]
        parts = info.split()
     
        pv_start = get_from_info(parts, "pv")
        if pv_start is None: 
            return
        
        engineMove = parts[pv_start + 1]
        engineName = self.engineFileNames[index]
        
        # Retrieve the score of the mainline (PV 1) after search is completed.
        # Note that the score is relative to the side to move.
        score_start = get_from_info(parts, "score")
        if score_start is None:
            return
        
        cp_marker = parts[score_start + 1]
        if cp_marker == "mate":
            # correct score if mating
            mate_moves= int(parts[score_start + 2])
            emit("info string mate detected in " + str(mate_moves) + " moves")
            if mate_moves > 0:
                cp = 30000 - (mate_moves * 10 )  # we do mate
            else:
                cp = -30000 + (mate_moves * 10 ) # we are mated
        else:
            cp = int(parts[score_start + 2])
            
        cp = cp / 100

        # log("info string pov score " + str(cp))    

        self._scores[index] = cp
        
        # white's view
        cpWhite = cp
        if not(self.board.turn):  # BLACK to move
            cpWhite = -cpWhite
        self._scores_white[index] = cpWhite

        # emit_and_log("info string final line " + engineName + ": " + info)
        emit_and_log("info string final eval " + engineName + ": bm " + str(engineMove) + ", sc " + str(cp))

        # set the move in the found moves
        self._moves[index] = engineMove
            
        # if all engines are done, and they agree on a move, do that move
        if self._moves[boss] is not None and self._moves[boss] == self._moves[counselor]:
            diff = self._scores[counselor] - self._scores[boss]
            self._printResult(boss, counselor, diff)
            emit_and_log("info string listening to boss: boss and counselor agree")
            self.listenedTo[boss] += 1
            self.agreed += 1
            bestMove = self._moves[boss]
            diff = self._scores[counselor] - self._scores[boss]
            if diff > 0:
                decider = counselor
            else:
                decider = boss

        # if counselor is much better than boss, do counselor's move
        elif self._moves[boss] is not None and self._moves[counselor] is not None:
            diff = self._scores[counselor] - self._scores[boss]
            self._printResult(boss, counselor, diff)
            if diff >= self.score_margin:
                emit_and_log("info string listening to counselor: which is stronger by {:2.2f}".format(diff))
                decider = counselor
            elif diff > 0:
                emit_and_log("info string listening to boss: counselor is stronger, but not enough, only {:2.2f}".format(diff))
                decider = boss
            else:
                emit_and_log("info string listening to boss: counselor is not stronger")
                decider = boss
                           
            self.listenedTo[decider] += 1
            bestMove = self._moves[decider]
                    
        # we dont know our best move yet!
        else:
            emit_and_log("info string dont know our best move yet")
            return

        # now we have our best move!
                                    
        # stop all engines
        self.send_command_to_engines("stop")
      
        
        # send final info to GUI
        emit_and_log(self._info[decider])
        
        # send bestmove result to GUI
        emit_and_log("bestmove " + str(bestMove))
        
        # pretty logging of bestmove
        move = chess.Move.from_uci(bestMove)
        san_bestmove = self.board.san(move)
        lan_bestmove = self.board.lan(move)
        logtext = "Move: " + str(self.board.fullmove_number) + ". "
        if (self.board.turn == chess.BLACK):
            logtext += "... "
        logtext += lan_bestmove + " (" + san_bestmove + ")"
        log(logtext)
        
        self._printStats()

        self._canceled = True

    # initialize infos
    def init_infos(self):
        self.listenedTo = [0, 0]
        self.agreed = 0


    # inverse of chess.emgine.parse_uci_info
    # make uci info string from dictionary
    def _make_uci_info_from_dict(self, kv_dict):
        result = []
        for i,j in kv_dict.items():
            if isinstance(j, int):
                result.append('%s %d' % (i,j))
            elif isinstance(j, float):
                result.append('%s %f' % (i,j))    
            elif isinstance(j, chess.engine.PovScore):
                if j.is_mate():
                    result.append('%s mate %s' % (i,j.pov(self.board.turn).mate()))   
                else:
                    result.append('%s cp %s' % (i,j.pov(self.board.turn).score()))             
            elif isinstance(j, list):
                result.append('%s ' % i)
                for m in j:
                    if isinstance(m, chess.Move):
                        result.append('%s' % m.uci())        
            else:
                result.append("%s '%s'" % (i,j))
                ## log(i + " is " + type(j).__name__)
        
        return ' '.join(result) 


    # handle UCI position command
    def _handle_position(self, positionInput):
        words = positionInput.split()
        # if this is not true, it is not a position command
        assert words[0] == "position"
        try:
            # handle building up the board from a FEN string
            if words[1] == "fen":
                rest = positionInput.split(' ', 2)[2]
                if "moves" in rest:
                    rest = rest.split()
                    fen, moves = " ".join(rest[:6]), rest[7:]
                    self.board.set_fen(fen)
                    for move in moves:
                        # emit("Adding " + move + " to stack")
                        self.board.push_uci(move)
                else:
                    self.board.set_fen(rest)
            # handle board from startpos command, building up the board with moves
            elif words[1] == "startpos":
                self.board.reset()
                for move in words[3:]:  # skip the first two words : 'position' and 'startpos'
                    # emit("Adding " + move + " to stack")
                    self.board.push_uci(move)
            else:
                emit("unknown position type")
        except Exception as e:
            emit("something went wrong with the position. Please try again")
            emit(e)

        # show the board
        # emit(self.board)


    # prints results of both engines
    def _printResult(self, boss, counselor, diff):
          emit_and_log("info string final results - boss: bm " +  str(self._moves[boss]) + " sc " + str(self._scores[boss])
                + " - counselor: bm " + str(self._moves[counselor]) + " sc " + str(self._scores[counselor])
                + " diff: {:2.2f}".format(diff))


    # prints stats on how often was listened to boss and how often to counselor
    def _printStats(self):
        winBoss, drawBoss, lossBoss = get_win_draw_loss_percentages(self._scores_white[0])
        emit_and_log("info string Boss      best move: " + str(self._moves[0]) + " score: " + str(self._scores[0])
                       + " white {:2.1f}% win, {:2.1f}% draw, {:2.1f}% loss".format(winBoss, drawBoss, lossBoss))
        winCounselor, drawCounselor, lossCounselor = get_win_draw_loss_percentages(self._scores_white[1])
        emit_and_log("info string Counselor best move: " + str(self._moves[1]) + " score: " + str(self._scores[1])
                      + " white {:2.1f}% win, {:2.1f}% draw, {:2.1f}% loss".format(winCounselor, drawCounselor, lossCounselor))
        emit_and_log("info string listen stats [Boss, Counselor] " + str(self.listenedTo))
        totalSum = self.listenedTo[0] + self.listenedTo[1] 
        bossSum = self.listenedTo[0] 
        bossPercent = (float(bossSum) / float(totalSum)) * 100.0
        emit_and_log("info string listen stats Boss {:2.1f} %".format(bossPercent))
        agreedPercent = (float(self.agreed) / float(totalSum)) * 100.0
        emit_and_log("info string Boss and Counselor agreed so far " + str(self.agreed) + " times, {:2.1f} % ".format(agreedPercent))
        
 
# UTILS

# This function flushes stdout after writing so the UCI GUI sees it
def emit(text):
    print(text, flush=True)
 

# This function logs only 
def log(text):
    logger.info(text)


# This function prints and logs 
def emit_and_log(text):
    emit(text)
    log(text)

    
def get_from_info(info, item):
    try:
        return info.index(item)
    except ValueError:
        return None
  

# get score as win/draw/loss percentages  
def get_win_draw_loss_percentages(pawn_value):
    ## w = 1 / (1 + pow( 10, (- (abs(pawn_value) / 4)))) * 100 # - 50 + (abs(pawn_value) / 10)
    ## q = (math.degrees(math.atan(abs(pawn_value) / 290.680623072))) / 1.548090806     
    ## w = q # * 5000 + 5000
    w = cp2q(abs(pawn_value)) * 100
    if (pawn_value >= 0):
        return w, 100 - w, 0
    else:
        return 0, 100 - w, w
    

# from lc0_analyzer-extras

def q2cp(q):
    return 290.680623072 * math.tan(1.548090806 * q) / 100.0

    # New formula is cp = 90 × tan(1.5637541897 × q)
    # doesnt work well here ?!
    # return 90 * math.tan(1.5637541897 * q)


def cp2q(cp):
    return math.atan(cp*100.0/290.680623072)/1.548090806

    # New formula is cp = 90 × tan(1.5637541897 × q), inverse:
    # return math.atan(cp/90)/1.5637541897
    # doesnt work well here ?!


# a stdout handler thread for an engine process
class EngineOutputHandler(threading.Thread):
    def __init__(self, proc, index, outer_class):
        threading.Thread.__init__(self)
        self.proc = proc
        self.index = index
        self.outer_class = outer_class
        

    def run(self):
        while self.proc.poll() == None:
            # log("waiting for info...")
            info = self.proc.stdout.readline().rstrip()
            # log("Got info: '" + info + "'")
            
            # call back
            self.outer_class._check_result(self.index, info)
            
            time.sleep(0.01) # needed for time control management
