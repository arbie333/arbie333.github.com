# A simple function to calculate the square of a number 
# the number to be squared is sent in the URL when we use GET 
# on the terminal type: curl http://127.0.0.1:5000 / home / 10 
# this returns 100 (square of 10) 

from flask import Blueprint, jsonify, request
from alak import *

test_blueprint = Blueprint('test_blueprint', __name__)

@test_blueprint.route('/hello', methods = ['GET', 'POST']) 
def home(): 
    if (request.method == 'GET'):
        data = "hello world"
        return jsonify({'data': data})

@test_blueprint.route('/square/<int:num>', methods = ['GET']) 
def disp(num): 
    return jsonify({'data': num**2})

@test_blueprint.route('/<int:old>/<int:new>', methods = ['GET']) 
def getJson(old, new):
    # add the method of the game and get the return value

    valid = True
    suicide = False
    captures = []
    old_position = 0
    new_position = 7
    board = []
    win = False

    jsonStr = jsonify({
        'valid': valid,
        'suicide': suicide,
        'captured': captures,
        'olg_position': old_position,
        'new_position': new_position,
        'board': board,
        'win': win
    })
    
    return jsonStr