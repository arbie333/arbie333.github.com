import pickle
import numpy as np
from itertools import product
import copy
import pickle
import json

class Alak:
    def __init__(self, moveX = 'random', moveO = 'random', print_result = False):
        self.board = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, -1, -1, -1, -1, -1], dtype=np.int8)
        self.board_size = len(self.board)
        self.boards = []

        self.x_pos = np.asarray(self.board>0).nonzero()[0]
        self.__pos = np.asarray(self.board==0).nonzero()[0]
        self.o_pos = np.asarray(self.board<0).nonzero()[0]
        
        self.print_result = print_result
        self.moveX = moveX
        self.moveO = moveO

        with open('my_training_model', 'rb') as file:
            self.clf = pickle.load(file)
        
        self.json = {
            'board': self.board.tolist(),
            'blackCaptured': [],
            'whiteCaptured': [],
            'old_position': int(-1),
            'new_position': int(-1),
            'suicide': False,
            'valid': True,
            'win': 0
        }

    def update_location(self):
        self.x_pos = np.asarray(self.board>0).nonzero()[0]
        self.__pos = np.asarray(self.board==0).nonzero()[0]
        self.o_pos = np.asarray(self.board<0).nonzero()[0]
    
    def move(self, turn, old, new):
        if turn == 1:
            if self.moveX == 'interactive':
                original_loc, next_loc, capture = self.move_interactive(turn, old, new)
            if self.moveX == 'model':
                original_loc, next_loc, capture = self.move_model(turn)

            self.json["blackCaptured"] = capture
            self.json['old_position'] = original_loc
            self.json['new_position'] = next_loc

        else:
            if self.moveO == 'interactive':
                original_loc, next_loc, capture = self.move_interactive(turn, old, new)
            if self.moveO == 'model':
                original_loc, next_loc, capture = self.move_model(turn)

            self.json['old_position'] = original_loc
            self.json['new_position'] = next_loc
            self.json["whiteCaptured"] = capture

        self.board[next_loc] = self.board[original_loc]
        self.board[original_loc] = 0

        self.update_location()
        self.json['board'] = self.board

        return original_loc, next_loc, capture
    
    def get_ori_loc(self, turn, original_loc):
        if turn == 1:
            pos = self.x_pos
            inputStr = 'x from: '
        else:
            pos = self.o_pos
            inputStr = 'o from: '
            
        # original_loc = int(input(inputStr))
        while original_loc not in pos:
            print('Invalid move: try again')
            original_loc = int(input(inputStr))
        
        return original_loc
    
    def get_next_loc(self, next_loc):
        # next_loc = int(input('move to: '))
        while next_loc not in self.__pos:
            print('Invalid move: try again')
            next_loc = int(input('move to: '))
        return next_loc
    
    def move_interactive(self, turn, old, new):
        if new not in self.__pos:
            self.json['valid'] = False
            return -1, -1, []
        
        original_loc = old
        next_loc = new

        b, capture = self.checkCapture(self.board, original_loc, next_loc, turn)
        if len(capture) == 0 and self.isSuicide(original_loc, next_loc, turn):
            print('{}->{} is a suicide move'.format(original_loc, next_loc))
            self.takeSuicide(original_loc, next_loc, turn)
            self.update_location()
            self.json['suicide'] = True
            print("suicide move")
        
        return original_loc, next_loc, capture
    
    def move_model(self, turn):
        clf = self.clf

        if turn == -1:
            # generate all kinds of board I can make after the input board
            moves = list(product(self.o_pos, self.__pos))

            # delete suicide moves
            dels = []
            for move in moves:
                b, capture = self.checkCapture(self.board, move[0], move[1], turn, change=False)
                if len(capture) == 0 and self.isSuicide(move[0], move[1], turn):
                    dels.append(move)
            for d in dels:
                moves.remove(d)
                
            boards = []
            for move in moves:
                new_board = copy.deepcopy(self.board)
                new_board, capture = self.checkCapture(new_board, move[0], move[1], turn)
                new_board[move[1]] = new_board[move[0]]
                new_board[move[0]] = 0
                boards.append(np.append(np.append(self.board, 2), new_board))

            proba = clf.predict_proba(boards)
            max_idx = np.argmax(proba[:, 0])

        else:
            moves = list(product(self.x_pos, self.__pos))
            
            # delete suicide moves
            dels = []
            for move in moves:
                b, capture = self.checkCapture(self.board, move[0], move[1], turn, change=False)
                if len(capture) == 0 and self.isSuicide(move[0], move[1], turn):
                    dels.append(move)
            for d in dels:
                moves.remove(d)
            
            probas = []
            for move in moves:
                new_board = copy.deepcopy(self.board)
                new_board, capture = self.checkCapture(new_board, move[0], move[1], turn)
                new_board[move[1]] = new_board[move[0]]
                new_board[move[0]] = 0
                
                __pos1 = np.asarray(self.board==0).nonzero()[0]
                o_pos1 = np.asarray(self.board<0).nonzero()[0]

                next_moves = list(product(__pos1, o_pos1))

                extended_boards = []
                for nm in next_moves:
                    next_board = copy.deepcopy(new_board)
                    next_board, capture = self.checkCapture(next_board, nm[0], nm[1], turn)
                    new_board[nm[1]] = new_board[nm[0]]
                    new_board[nm[0]] = 0
                    extended_boards.append(np.append(np.append(new_board, 2), next_board))

                proba = clf.predict_proba(extended_boards).sum(0)
                probas.append(proba)

            probas = np.array(probas)
            max_idx = np.argmax(probas[:, 1])
        
        original_loc, next_move = moves[max_idx][0], moves[max_idx][1]
        b, capture = self.checkCapture(self.board, original_loc, next_move, turn)
        self.update_location()
        return original_loc, next_move, capture
    
    def isSuicide(self, original_loc, next_move, turn):
        # EDGE
        if next_move == 0 or next_move == self.board_size - 1:
            return False
        
        # RIGHT
        right_enemy = False
        right = next_move + 1
        
        while right < self.board_size-1 and self.board[right] == turn:
            if right == original_loc:
                return False
            right += 1
            
        if self.board[right] == turn * -1:
            right_enemy = True

        # LEFT
        left_enemy = False
        left = next_move - 1
        
        while left > 0 and self.board[left] == turn:
            if left == original_loc:
                return False
            left -= 1
            
        if self.board[left] == turn * -1:
            left_enemy = True
        
        # BOTH
        if left_enemy and right_enemy:
            return True
        else:
            return False
        
    def takeSuicide(self, original_loc, next_move, turn):
        self.board[next_move] = 0
        self.board[original_loc] = 0
        # RIGHT
        right = next_move + 1

        while right < self.board_size-1 and self.board[right] == turn:
            self.board[right] = 0
            right += 1
            
        # LEFT
        left = next_move - 1

        while left > 0 and self.board[left] == turn:
            self.board[left] = 0
            left -= 1
    
    def checkCapture(self, board, original_loc, next_move, turn, change=True):
        capture = []
        size = len(board)
        
        # capture left
        if next_move > 0:
            left = next_move - 1

            while left > 0 and board[left] == -1 * turn:
                left -= 1

            if board[left] == turn and left != original_loc:
                for i in range(left+1, next_move):
                    if change:
                        board[i] = 0
                        capture.append(i)
        
        #capture right
        if next_move < size - 1:
            right = next_move + 1

            while right < size - 1 and board[right] == -1 * turn:
                right += 1

            if board[right] == turn and right != original_loc:
                for i in range(next_move + 1, right):
                    if change:
                        board[i] = 0
                        capture.append(i)

        return board, capture
        
    def one_round(self, old, new):
        # x move
        turn = 1
        gain = self.move(turn, old, new)

        if self.won() == 1:
            return gain

        # o move
        turn = -1
        gain = self.move(turn, old, new)
        
        return gain
        
    def won(self): # 1 -> x won, 0 -> keep playing, -> -1 -> o won
        if len(self.o_pos) <= 1:
            return 1
        elif len(self.x_pos) <= 1:
            return -1
        else:
            return 0

    def getNext(self, old, new, board):
        boardLst = [int(i) for i in board.split(',')]

        self.board = np.array(boardLst, dtype=np.int8)
        self.update_location()
        self.one_round(old, new)

        self.json['win'] = self.won()
        self.json['board'] = self.board.tolist()
        self.json['old_position'] = int(self.json['old_position'])
        self.json['new_position'] = int(self.json['new_position'])

        # self.json['captured'] = self.json['captured']
        jsonStr = json.dumps(self.json, indent = 4)
        print('------------- end one round --------------')

        return jsonStr

if __name__ == "__main__":
    alak = Alak(moveX='interactive', moveO='model', print_result=True)
    board = [ 1, 1, 1, 1, 1, 0, 0, 0, 0, -1, -1, -1, -1, -1 ]
    alak.getNext(0, 1, board)