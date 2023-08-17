from engine import GameState
import support as sp
import numpy as np
import pygame as py

py.init()

# constants
W, H = 640, 640
SQ = W / 8
FPS = 30

# Import PNGs of Pieces
IMAG = []
all_pieces = py.image.load('chess_pieces.png')
# maps bitboard position to imag position
pm = {0:6, 1:7, 2:8, 3:9, 4:10, 5:11, 6:0, 7:1, 8:2, 9:3, 10:4, 11:5}
for row in range(2):
    for i in range(6):
        IMAG.append(py.transform.scale(all_pieces.subsurface((i * 132, row * 132, 132, 132)), (SQ, SQ)))

# Colors for dark and light squares 
#BOARD_COLORS = (py.Color(228,234,193), py.Color(101, 137, 67)) # chess.comm color theme
#BOARD_COLORS = (py.Color('light grey'), py.Color('cadetblue4'))
BOARD_COLORS = (py.Color(254, 203, 136), py.Color(159, 90, 50))
HIGHLIGHT_COLOR = py.Color('yellowgreen')
TARGET_COLOR = py.Color('sienna3')


def main():
    '''
    Main Function, includes game loop
    '''
    screen = py.display.set_mode((W,H))
    clock = py.time.Clock()
    screen.fill(BOARD_COLORS[0])

    state = GameState()
    Square_highlighted = None
    legal_moves = np.uint64(0)

    running = True
    while running:
        for event in py.event.get():
            if event.type == py.QUIT:
                running = False

            if event.type == py.MOUSEBUTTONDOWN:
                # make moves 
                
                if Square_highlighted == None:
                    fr = np.left_shift(1, coordinates_to_sq_nr(py.mouse.get_pos()), dtype=np.uint64)
                    if (state.White_to_move and fr & state.white != 0) or (not state.White_to_move and fr & state.black !=0):
                        Square_highlighted = coordinates_to_sq_nr(py.mouse.get_pos())
                        legal_moves = state.Generate_legal_moves(Square_highlighted)

                else:
                    move_try = (Square_highlighted, coordinates_to_sq_nr(py.mouse.get_pos()))
                    to = np.left_shift(1, move_try[1], dtype=np.uint64)
                    if legal_moves & to != 0:
                        state.make_move(move_try)
                        
                    Square_highlighted = None
                    legal_moves = np.uint64(0)

  
        draw(screen, state, Square_highlighted, legal_moves)
        clock.tick(FPS)


def draw(screen:py.Surface, state:GameState, highlight, legal_moves): 
    screen.fill(BOARD_COLORS[0])
    draw_board(screen)
    if legal_moves:
        highlight_possible_moves(screen, legal_moves)
    draw_pieces(screen, state, highlight)
    py.display.flip()


def draw_board(screen:py.Surface):
    for r in range(8):
        for f in range(4):
            screen.fill(BOARD_COLORS[1], py.Rect(SQ * ((r%2 == 0)+2*f), r*SQ, SQ, SQ))

def draw_pieces(screen:py.Surface, state:GameState, highlight):
    '''
    Draws all the pieces on the Board according to bitmap position from GameState
    '''
    for sq in range(0,64):
        piece = state.figure_on_square(sq)
        if type(piece) == int:
            file = sq % 8
            rank = 7 - sq // 8
            # highlight chosen square
            if sq == highlight:
                screen.fill(HIGHLIGHT_COLOR, py.Rect(file*SQ, rank*SQ, SQ, SQ))
            screen.blit(IMAG[int(pm.get(piece))], py.Rect(file*SQ, rank*SQ, SQ, SQ)) # type: ignore
   
def highlight_possible_moves(screen:py.Surface, legal_moves):
    '''
    highlight all possible target squares of a chosen piece
    '''
    
    string_legal = np.binary_repr(legal_moves, width=64)[::-1]
    for sq in range(0,64):
        if string_legal[sq] == '1':
            file = sq % 8
            rank = 7 - sq // 8
            screen.fill(TARGET_COLOR, py.Rect(file * SQ, rank * SQ, SQ, SQ))

def coordinates_to_sq_nr(pos):
    ''' 
    Return sq_nr between 0 and 63 
    '''
    rank = 7 - (pos[1] // SQ)
    file = pos[0] // SQ
    return int((rank * 8) + file)


if __name__ == '__main__':
    main()