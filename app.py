from flask import Flask, render_template
import alak # the alak playing model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    model_moves = [0, 1]
    return render_template('game.html', model_moves=model_moves)

@app.route('/move/<int:old>/<int:new>/<board>')
def get_move(old, new, board):
    game = alak.Alak(moveX='interactive', moveO='model', print_result=True)
    json = game.getNext(old, new, board)

    return json

@app.route('/record')
def record():
    return render_template('record.html')

@app.route('/ranking')
def ranking():
    return render_template('ranking.html')

@app.route('/signIn')
def signIn():
    return render_template('signIn.html')

@app.route('/signUp')
def signUp():
    return render_template('signUp.html')

if __name__ == "__main__":
    app.run()