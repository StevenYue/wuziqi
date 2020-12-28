#!/usr/bin/python3.8

from threading import Lock
import json
import logging
import time

PLAYER_ID_0 = 0
PLAYER_ID_1 = 1

class Game:
    class STATE:
        WAITING = 0 # waiting for JOIN or READY
        START = 1
        FINISH = 2

    class Player:
        def __init__(self, name, game_size):
            self.name = name
            self.moves = [[0] * game_size] * game_size 
            self.win_cnt = 0
            self.ready = False

    def __init__(self, size=15):
        assert size >= 5
        self.size = size
        self.players = {
            PLAYER_ID_0: None,
            PLAYER_ID_1: None,
        }
        self.game_state = None
        self.game_cnt = 0
        self.whos_turn = 0 
        self.winner = None
        self.mutex = Lock()
        self.bd = int(time.time())

    def _in_board(self, x, y):
        return x >= 0 and x < self.size and y >= 0 and y < self.size

    def _get_obj(self):
        obj = {
            "game_index" : self.game_cnt,
            "whos_turn" : self.whos_turn,
            "winner" : self.winner,
            "state" : self.game_state,
            "bd" : self.bd,
            "P0" : self.players[PLAYER_ID_0].__dict__ if self.players[PLAYER_ID_0] else None,
            "P1" : self.players[PLAYER_ID_1].__dict__ if self.players[PLAYER_ID_1] else None,
        }
        return obj

    # given a list of hashes and see if it won
    # true if the move set won, false otherwise
    def _is_moves_won(self, moves):
        row_checker = 0 
        col_checker = [0] * self.size
        quad_checker_len = self.size * 2 - 9
        quad13_checker = [0] * quad_checker_len
        quad24_checker = [0] * quad_checker_len
        for i in range(0, self.size):
            row_checker = 0
            for j in range(0, self.size):
                quad13_index = i + j - 4
                quad24_index = i - j + self.size - 5
                if 0 == moves[i][j]: 
                    row_checker = 0
                    col_checker[j] = 0
                    if quad13_index >= 0 and quad13_index < quad_checker_len:
                        quad13_checker[quad13_index] = 0
                    if quad24_index >= 0 and quad24_index < quad_checker_len:
                        quad24_checker[quad24_index] = 0
                    continue
                row_checker += 1
                col_checker[j] += 1 
                if quad13_index >= 0 and quad13_index < quad_checker_len:
                    quad13_checker[quad13_index] += 1
                if quad24_index >= 0 and quad24_index < quad_checker_len:
                    quad24_checker[quad24_index] += 1
                if 5 == row_checker \
                    or 5 == col_checker[j] \
                    or (quad13_index >= 0 and quad13_index < quad_checker_len and 5 == quad13_checker[quad13_index]) \
                    or (quad24_index >= 0 and quad24_index < quad_checker_len and 5 == quad24_checker[quad24_index]):
                    return True
        return False

    # TODO:
    # start a new game, reset state & counter ...
    def start_new_game(self):
        pass 

    # TODO
    def finish_up_a_game(player_id):
        pass

    # TODO:
    # Add a player to the game,
    # return player Id on success, None on failer
    def add_player(self, name):
        return None
    
    # TODO:
    # mark player_id as ready
    def player_ready(self, player_id):
        pass

    def switch_turn(self):
        self.whos_turn = PLAYER_ID_0 if self.whos_turn == PLAYERD_ID_1 else PLAYERD_ID_1

    # add a piece to the board, 
    # return 0 on success, -1 on failure
    def add_move(self, player_id, x, y):
        with self.mutex:
            player = self.players[player_id]
            if self.whos_turn == player_id and _is_board(x, y) and 0 == player.moves[x][y]:
                player.moves[x][y] = 1
                if self._is_moves_won(player.moves):
                    finish_up_a_game(player_id) 
                self.switch_turn()
                return 0
            else:
                logging.error("Invalid input:%s, %s, %s, %s", player_id, x, y, self._get_obj())
                return -1

    # determin who should start first
    def who_start_first(self):
        return PLAYER_ID_0 if self.game_cnt % 2 == 0 else PLAYER_ID_1

    # serialize for sending over wire
    def serialize(self):
        with self.mutex:
            obj = self._get_obj()
        return json.dumps(obj) 

