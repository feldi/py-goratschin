#!/usr/bin/env python3

# to create an EXE from this file, do:
# pip install pyinstaller
# pyinstaller -wF goratschinLauncher.py
# copy .exe from 'dist' directory in root directory

import argparse
import logging
import sys

# import asyncio
# import chess.engine

from goratschinChess import GoratschinChess


# file names for the engines. YOU CAN CHANGE THESE
engineFolder = "./engines/"
engineFileNames = ["lc0.exe", "stockfish_10_x64.exe"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UCI ches engine.')
    parser.add_argument('-log', help='Name of log file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('-m', '--margin', type=int, default=50, help="Margin in centipawns of which the counselor's eval must be better than the boss.")
    args = parser.parse_args()

    # configure logging

    logger = logging.getLogger("goratschinChess")   
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO) 
    #c_handler = logging.StreamHandler(sys.stdout)
    #c_format = logging.Formatter('%(asctime)s - %(message)s')
    #c_handler.setFormatter(c_format)
    #logger.addHandler(c_handler)
    if args.log:
        f_handler = logging.FileHandler(args.log)
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)
        # print('logfile specified: ' + args.log, flush=True)
    # print('margin specified: ' + str(args.margin), flush=True)
    
    # This starts the goratschinChess engine
    GoratschinChess(engineFolder, engineFileNames, args.margin).start()
