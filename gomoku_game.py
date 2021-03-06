#!/usr/bin/python3

from threading import Lock, Thread
import json
import logging
import time

PLAYER_ID_0 = 0
PLAYER_ID_1 = 1
FRAME_RATE_SEC = 5.0
STALE_GAME_THRESHOLD_SEC = 120

class Game:
    class STATE:
        WAITING = 0 # waiting for JOIN or READY
        START = 1
        FINISH = 2
        STALE = 3

    class Player:
        def __init__(self, name, game_size):
            self.name = name
            self.win_cnt = 0
            self.lose_cnt = 0
            self.ready = True
            self.game_size = game_size
            self.reset_moves()

        def reset_moves(self):
            self.moves = [[0 for i in range(self.game_size)] for j in range(self.game_size)] 

    def __init__(self, size=15):
        assert size >= 5
        self.size = size
        self.players = {}
        self.game_state = self.STATE.WAITING
        self.game_cnt = 0
        self.whos_turn = 0
        self.p0 = None
        self.p1 = None
        self.winner = None
        self.updater = None
        self.mutex = Lock()
        self.last_action_ts = None
        self.bd = int(time.time())

    def _in_board(self, x, y):
        return x >= 0 and x < self.size and y >= 0 and y < self.size

    def _get_obj(self):
        obj = {
            "game_cnt" : self.game_cnt,
            "whos_turn" : self.whos_turn,
            "winner" : self.winner,
            "state" : self.game_state,
            "bd" : self.bd,
            "P0" : self.p0.__dict__ if self.p0 else None,
            "P1" : self.p1.__dict__ if self.p1 else None,
        }
        return obj

    def get_obj(self):
        with self.mutex:
            return self._get_obj()

    def valid_player_id(self, player_id):
        return player_id in [PLAYER_ID_0, PLAYER_ID_1]

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

    # start a new game, reset state & counter ...
    def start_new_game(self):
        self.game_cnt += 1
        self.game_state = self.STATE.START 
        self.winner = None
        self.whos_turn = self.who_start_first()
        self.p0.reset_moves()
        self.p1.reset_moves()

    def finish_up_a_game(self, winner_player_id):
        self.game_state = self.STATE.FINISH 
        self.winner = winner_player_id
        if self.winner == PLAYER_ID_0:
            self.p0.win_cnt += 1
            self.p1.lose_cnt += 1
        else:
            self.p0.lose_cnt += 1
            self.p1.win_cnt += 1
        self.p0.ready = False
        self.p1.ready = False

    # Add a player to the game,
    # return player Id on success, None if can't add 
    def add_player(self, name, player_id):
        with self.mutex:
            if None == player_id:
                if None != self.p0 and None != self.p1:
                    return None
                new_player = self.players[name] if name in self.players else self.Player(name, self.size)
                self.players[name] = new_player
                if None == self.p0:   
                    self.p0 = new_player
                    player_id = PLAYER_ID_0
                else:
                    self.p1 = new_player
                    player_id = PLAYER_ID_1
            else:
                if player_id == PLAYER_ID_0:
                    self.p0 = self.players[name]
                    self.p0.ready = True
                else:
                    self.p1 = self.players[name]
                    self.p1.ready = True
            self.game_state = self.STATE.WAITING
            if self.p0 and self.p0.ready and self.p1 and self.p1.ready:
                self.start_new_game()
            self.update_last_action_ts()
        logging.info("Adding player %s, as Id: %s", name, player_id)
        return player_id

    def player_surrender(self, player_id):
        with self.mutex:
            if self.game_state == self.STATE.STALE:
                return
            self.update_last_action_ts()
            self.finish_up_a_game(PLAYER_ID_1 if player_id == PLAYER_ID_0 else PLAYER_ID_0) 

    def player_leave(self, player_id):
        with self.mutex:
            if self.game_state == self.STATE.STALE:
                return
            self.game_state = self.STATE.WAITING
            if PLAYER_ID_0 == player_id:
                if self.p0:
                    self.p0.ready = False
                    self.p0 = None
            elif PLAYER_ID_1 == player_id:
                if self.p1:
                    self.p1.ready = False
                    self.p1 = None
            else:
                logging.error("Player_leave bad player_id: %s", player_id)

    # add a piece to the board, 
    # return 0 on success, -1 on failure
    def add_move(self, player_id, x, y):
        logging.info("add_move:%s, %s, %s", player_id, x, y)
        with self.mutex:
            if self.game_state == self.STATE.STALE:
                return
            player = self.p0 if player_id == PLAYER_ID_0 else self.p1
            if self.whos_turn == player_id and self._in_board(x, y) and 0 == player.moves[x][y]:
                player.moves[x][y] = 1
                if self._is_moves_won(player.moves):
                    self.finish_up_a_game(player_id) 
                else:
                    self.switch_turn()
                self.update_last_action_ts()
                return 0
            else:
                logging.error("Invalid input:%s, %s, %s, %s", player_id, x, y, self._get_obj())
                return -1
    
    def switch_turn(self):
        self.whos_turn = PLAYER_ID_0 if self.whos_turn == PLAYER_ID_1 else PLAYER_ID_1

    # determin who should start first
    def who_start_first(self):
        return PLAYER_ID_0 if self.game_cnt % 2 == 1 else PLAYER_ID_1
  
    def update_last_action_ts(self):
        self.last_action_ts = int(time.time())
        
    def game_stale(self):
        now = int(time.time())
        with self.mutex:
            if None != self.last_action_ts \
                and STALE_GAME_THRESHOLD_SEC < (now - self.last_action_ts):
                return True
            else:
                return False

    def reset(self):
        self.game_cnt = 0
        self.whos_turn = 0
        self.p0 = None
        self.p1 = None
        self.winner = None
        self.updater = None
        self.last_action_ts = None

    def callback(self, func, *args):
        while True:
            func(*args)
            time.sleep(FRAME_RATE_SEC)
            if (None == self.p0 and None == self.p1) or self.game_stale():
                self.reset()
                self.game_state = self.STATE.STALE
                func(*args)
                self.updater = None
                return

    def start_refresher(self, func, *args):
        with self.mutex:
            if not self.updater: 
                self.updater = Thread(target=self.callback, args=(func,*args,), daemon=True)
                self.updater.start()

