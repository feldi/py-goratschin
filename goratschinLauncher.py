#!/usr/bin/env python3

# to create an EXE from this file, do:
# pip install pyinstaller
# pyinstaller -wF goratschinLauncher.py
# copy .exe from 'dist' directory in root directory

import argparse
import logging
import sys
import datetime

# import asyncio
# import chess.engine

from goratschinChess import GoratschinChess


# file names for the engines. YOU CAN CHANGE THESE
engineFolderDefault = "./engines/"
engineFileNames = ["lc0.exe", "stockfish.exe"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UCI ches engine.')
    parser.add_argument('-log', help='Name of log file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('-e', '--engineFolder', help='Engine folder.')
    parser.add_argument('-m', '--margin', type=int, default=50, help="Margin in centipawns of which the counselor's eval must be better than the boss.")
    args = parser.parse_args()

    print('args :'  + str(args), flush=True)

    # configure logging

    logger = logging.getLogger("goratschinChess")   
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO) 
    #c_handler = logging.StreamHandler(sys.stdout)
    #c_format = logging.Formatter('%(asctime)s - %(message)s')
    #c_handler.setFormatter(c_format)
    #logger.addHandler(c_handler)
    if args.log:
        now = datetime.datetime.now()
        f_handler = logging.FileHandler(args.log + '-' + str(now)[:10] + ".log")
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)
        # print('logfile specified: ' + args.log, flush=True)
    # print('margin specified: ' + str(args.margin), flush=True)
    
    enginesDir = args.engineFolder if args.engineFolder else engineFolderDefault
    
    print('engine folder specified: ' + str(enginesDir), flush=True)

    # This starts the goratschinChess engine
    GoratschinChess(enginesDir, engineFileNames, args.margin).start()

    # import sys
    # print(sys.executable)
                        