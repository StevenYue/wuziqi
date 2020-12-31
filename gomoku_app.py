#!/usr/bin/python3.8

from flask import Flask, render_template
from flask_socketio import SocketIO
from gomoku_game import Game
import logging

game = Game()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

PLAYER_POOL = set(["luyixuan",'yuexiang','gebingqing','zhangshuqin','yuejiajia','lubin']);

ERROR_CODE = {
    "INVALID_USER" : -1,
    "GAME_FULL" : -2,
}

def refresh():
    while True:
        time.sleep(FRAME_RATE_SEC)
        send_game_data()

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

@socketio.on("ready")
def player_ready_handler(args):
    player_id = args["player_id"]
    player_name = args["player_name"]
    if None == player_id:
        if player_name.lower() not in PLAYER_POOL:
            send("ready", ERROR_CODE["INVALID_USER"])
        else:
            new_id = game.add_player(player_name)
            if None == new_id:
                send("ready", ERROR_CODE["GAME_FULL"])
            else:
                send("ready", new_id)
                game.start_refresher(send_game_data)
    else:
        if game.valid_player_id(player_id):
            game.player_ready(player_id)
        else:
            send("ready", ERROR_CODE["INVALID_USER"])


@socketio.on("put_piece")
def player_ready_handler(args):
    player_id = args["player_id"]
    x = args["x"]
    y = args["y"]
    game.add_move(player_id, x, y)

@socketio.on("dummy")
def dummy_handler(args):
    print("dummmmmmmmmmmmy:", args)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)

