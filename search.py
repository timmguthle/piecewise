import numpy as np
import random
import multiprocessing
from engine import GameState
import support as sp

# Piece values
PAWN = 100
KINGHT = 300
BISHOP = 310 # could maybe also depend on the numbers of figures still on the board
ROOK = 500
QUEEN = 900

q = multiprocessing.Queue()

def return_Queue():
    return q.get()


def find_move(valid_moves):
    move = random.choice(valid_moves)
    return move

def search(state:GameState, depth):
    '''
    this function is called recursivly and returns the best possible evaluation that can be reached with one move 

    simple min-max search algorithm. Use of NegaMax to use only one instead of two functions
    '''
    # at max depth just return the evaluation without calculating the possible moves. so check at beginning of function
    if depth == 0:
        return evaluation(state)

    valid_moves = state.generate_all_valid_moves()
    if len(valid_moves) == 0:
        if state.determin_result() == 0:
            return 0 # stalemate
        else:
            return - np.inf # no moves avalible so whoevers turn it is has lost.

    # define best evaluation as - infinity to be overwritten by eval search
    best_eval = -np.inf

    if depth != 0:
        for move in valid_moves:
            state.make_move(move)
            eval = - search(state, depth - 1) # each time the function is called the perspective changes so the sign must be flipped!!
            best_eval = max(best_eval, eval)
            state.unmake_move()
            # choose highest evaluation of this function call

    return best_eval

def initial_search(valid_moves, state:GameState, depth):
    '''
    function called at the beginning of the search 

    this function calls the search function which then gets called recursivly
    '''
    
    # here move ordering later

    # define best evaluation as - infinity to be overwritten by eval search
    best_eval = - np.inf
    best_move = 0

    for move in valid_moves:
        state.make_move(move)
        eval = - search(state, depth - 1) # each time the function is called the perspective changes so the sign must be flipped!!
        if eval > best_eval:
            best_eval = eval
            best_move = move
        state.unmake_move()
        
    print(best_eval)
    print(best_move)
    return best_move


def evaluation(state:GameState) -> float:
    # evaluate the position based on material differance
    eval = count_material(state, True) - count_material(state, False) # white - black material

    return eval * ((1 * state.White_to_move) + (not state.White_to_move) * -1)

def count_material(state, white):
    count = 0
    if white: # White pieces
        set = (6,7,8,9,11) # state.p indices for correct piecetype
    else:
        set = (0,1,2,3,5)

    count += sp.count_set_bits(state.p[set[0]]) * PAWN
    count += sp.count_set_bits(state.p[set[1]]) * ROOK
    count += sp.count_set_bits(state.p[set[2]]) * KINGHT
    count += sp.count_set_bits(state.p[set[3]]) * BISHOP
    count += sp.count_set_bits(state.p[set[4]]) * QUEEN

    return count