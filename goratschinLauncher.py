#!/usr/bin/env python3

import argparse
import logging

##import asyncio
## import chess.engine

from goratschinChess import GoratschinChess


# file names for the engines. YOU CAN CHANGE THESE
engineFolder = "./engines"
engineFileNames = ["lc0.exe", "stockfish_10_x64.exe"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    args = parser.parse_args()

    logger = logging.basicConfig(level=logging.DEBUG if args.v else logging.INFO)
    ## logger = logging.basicConfig(level=logging.DEBUG)

    # This starts combichess. Do NOT change or remove this!
    GoratschinChess(engineFolder, engineFileNames).start()
    
    ## asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
    ## asyncio.run(CombiChess(engineFolder, engineFileNames).start())
