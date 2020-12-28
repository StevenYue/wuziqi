#!/usr/bin/python3.8

from flask import Flask, render_template
from gomoku_game import Game

game = Game()
app = Flask(__name__)

@app.route('/')
def index_page():
    return render_template("index.html")

@app.route('/gamedata')
def test_game_data():
    return game.serialize()

