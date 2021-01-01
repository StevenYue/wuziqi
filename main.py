#!/usr/bin/python3

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from gomoku_game import Game
import logging
from logging.handlers import RotatingFileHandler

game = Game()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=False, engineio_logger=False, cors_allowed_origins="*")

PLAYER_POOL = set(["luyixuan",'yuexiang','gebingqing','zhangshuqin','yuejiajia','lubin']);

ERROR_CODE = {
    "INVALID_USER" : -1,
    "GAME_FULL" : -2,
}


def send(event, data):
    socketio.emit(event, data)

def send_game_data():
    send("game_data", game.get_obj())

@app.route('/')
def index_page():
    return render_template("index.html")

@app.route('/monster')
def monster_page():
    return render_template("monster.html")

@app.route("/ready", methods=['POST'])
def player_ready_handler():
    data = request.json
    logging.info("player_ready_handler:%s", data)
    player_id = data["player_id"]
    player_name = data["player_name"]
    logging.info("player_ready, %s, %s,", player_id, player_name)
    if player_name.lower() not in PLAYER_POOL:
        return {"rc":ERROR_CODE["INVALID_USER"]}
    else:
        new_id = game.add_player(player_name, player_id)
        if None == new_id:
            return {"rc":ERROR_CODE["GAME_FULL"]}
        else:
            send_game_data()
            return {"rc":0, "player_id":new_id}

@socketio.on("game_data")
def put_piece_handler():
    send_game_data()

@socketio.on("put_piece")
def put_piece_handler(args):
    logging.info("put_piece: %s", args)
    player_id = args["player_id"]
    x = args["x"]
    y = args["y"]
    game.add_move(player_id, x, y)
    send_game_data()

@socketio.on("leave")
def leave_handler(args):
    logging.info("leave: %s", args)
    player_id = args["player_id"]
    game.player_leave(player_id)
    send_game_data()

@socketio.on("surrender")
def surrender_handler(args):
    logging.info("surrender: %s", args)
    player_id = args["player_id"]
    game.player_surrender(player_id)
    send_game_data()

if __name__ == '__main__':
    logging.basicConfig(
        handlers=[RotatingFileHandler('./gomoku.log', maxBytes=2000000, backupCount=5)],
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')
    
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)

    logging.info("Gomoku started")
    socketio.run(app, host='0.0.0.0', debug=True)

