import numpy as np

print('import done')

# define usefull bitboards

clip = np.array(
    [18374403900871474942, 18302063728033398269, 18157383382357244923, 17868022691004938231, 17289301308300324847, 16131858542891098079, 13816973012072644543, 9187201950435737471],
    dtype=np.uint64
)


rank = np.array(
     [255, 65280, 16711680, 4278190080, 1095216660480, 280375465082880, 71776119061217280, 18374686479671623680],
     dtype=np.uint64
)

file = clip ^ np.uint64(2**64 - 1)

edge_mask = rank[0] | rank[-1] | file[0] | file[-1]
castl_mask = np.array([1008806316530991104, 6917529027641081856, 14, 96], dtype=np.uint64) # Order: BQ, BK, WQ, WK

def print_nice_bitboard(b):
    s = np.binary_repr(b, width=64)
    for i in range(8):
        rank = s[i*8:(i*8)+8]
        print(rank[::-1])

# precompute legal_moves list 
legal_moves = np.zeros((5, 64), dtype=np.uint64)

# precompute array with all moves a knight can make on any position
def knight_moves(sq_nr, clip):
        '''
        This function computes all valid knight moves for a given knight position
        
        returns bitboard with valid moves
        '''
        pos = np.left_shift(1, sq_nr, dtype=np.uint64)

        spot1 = (pos & clip[0] & clip[1]) << np.uint(6)
        spot2 = (pos & clip[0]) << np.uint(15)
        spot3 = (pos & clip[-1]) << np.uint(17)
        spot4 = (pos & clip[-2] & clip[-1]) << np.uint(10)
        spot5 = (pos & clip[-2] & clip[-1]) >> np.uint(6)
        spot6 = (pos & clip[-1]) >> np.uint(15)
        spot7 = (pos & clip[0]) >> np.uint(17)
        spot8 = (pos & clip[0] & clip[1]) >> np.uint(10)

        knight_moves = spot1 | spot2 | spot3 | spot4 | spot5 | spot6 | spot7 | spot8

        return knight_moves


def king_moves(sq_nr, clip):
    '''
    This function computes all valid king moves for a given king position and color
    
    returns bitboard with valid moves
    '''
    pos = np.left_shift(1, sq_nr, dtype=np.uint64)

    spot1 = (pos & clip[0]) << np.uint64(7)
    spot2 = pos << np.uint64(8)
    spot3 = (pos & clip[-1]) << np.uint64(9)
    spot4 = (pos & clip[-1]) << np.uint64(1)
    spot5 = (pos & clip[-1]) >> np.uint64(7) 
    spot6 = pos >> np.uint64(8)
    spot7 = (pos & clip[0]) >> np.uint64(9)
    spot8 = (pos & clip[0]) >> np.uint64(1)

    king_moves = spot1 | spot2 | spot3 | spot4 | spot5 | spot6 | spot7 | spot8
    return king_moves

def rook_moves_empty_board(sq_nr):
    '''
    returns bitboard of all the position a Rook can move on an empty board
    '''
    pos = np.left_shift(1, sq_nr, dtype=np.uint64)
    spot_rank = rank[sq_nr // 8] ^ pos
    spot_file = file[sq_nr % 8] ^ pos

    rook_moves = spot_rank | spot_file
    return rook_moves






def bishop_moves_empty_board(sq_nr):
    pos = np.left_shift(1, sq_nr, dtype=np.uint64)
    spots = pos

    rank = sq_nr // 8
    file = sq_nr % 8

    for i in range(min(7-rank, 7-file)): # type: ignore
        spots |= np.left_shift(1, sq_nr + (9*(i+1)), dtype=np.uint64)
    for i in range(min(rank, 7-file)): # type: ignore
        spots |= np.left_shift(1, sq_nr - (7*(i+1)), dtype=np.uint64)
    for i in range(min(rank, file)): # type: ignore
        spots |= np.left_shift(1, sq_nr - (9*(i+1)), dtype=np.uint64)
    for i in range(min(7-rank, file)): # type: ignore
        spots |= np.left_shift(1, sq_nr + (7*(i+1)), dtype=np.uint64)
         

    bishop_moves = spots ^ pos
    return  bishop_moves


# order: N, K, B, R, Q
for square in range(64):
     legal_moves[0][square] = knight_moves(square, clip)
     legal_moves[1][square] = king_moves(square, clip)
     legal_moves[2][square] = bishop_moves_empty_board(square)
     legal_moves[3][square] = rook_moves_empty_board(square)
     legal_moves[4][square] = legal_moves[2][square] | legal_moves[3][square]


# legal moves [3] = rook attacks on empty board

def rook_moves_with_blockers(sq:int) -> np.ndarray:
    '''
    This function computes the legal move a rook can make on one sq with all possible blocking configurations

    return list with blocking bitboard and attack bitboard. blockers are treated as enemy pieces, so they can be captured

    '''
    a = legal_moves[3][sq]
    numbers = np.arange(0, (2**14), dtype=np.uint64)
    config = np.zeros((2**14), dtype=np.uint64) # store all blocking configurations
    attack_set = np.zeros((2**14), dtype=np.uint64) # store all attacking configurations

    a_list = [] # generate list with index where a = 1. allways length 14
    while a:
        lsb = a & -a
        a_list.append(np.uint64(np.log2(lsb)))
        a ^= lsb

    for i in numbers:
        blocks = np.uint64(0)
        for j,b in enumerate(np.binary_repr(i, width=14)[::-1]):
            blocks |= np.left_shift(int(b), a_list[j], dtype=np.uint64)
        config[i] = blocks # add blocker config to list 
        attack_set[i] = moves_from_blocker_config_rook(sq, blocks)

    return config


def bishop_moves_with_blockers(sq:int) -> np.ndarray:
    '''
    This function computes the legal move a bishop can make on one sq with all possible blocking configurations

    return list with blocking bitboard and attack bitboard. blockers are treated as enemy pieces, so they can be captured

    '''
    a = legal_moves[2][sq]
    a_list = [] # generate list with index where a = 1. variable length between 7 and 13
    while a:
        lsb = a & -a
        a_list.append(np.uint64(np.log2(lsb)))
        a ^= lsb
    nr_moves = len(a_list)

    numbers = np.arange(0, (2**nr_moves), dtype=np.uint64)
    config = np.zeros((2**13), dtype=np.uint64) # store all blocking configurations padded with zeros
    attack_set = np.zeros((2**13), dtype=np.uint64) # store all attacking configurations padded with zeros


    for i in numbers:
        blocks = np.uint64(0)
        for j,b in enumerate(np.binary_repr(i, width=nr_moves)[::-1]): # move the bits of numbers to the relevant position given by sq
            blocks |= np.left_shift(int(b), a_list[j], dtype=np.uint64)
        config[i] = blocks
        attack_set[i] = moves_from_blocker_config_bishop(sq, blocks, legal_moves[2][sq])

    return config


def moves_from_blocker_config_bishop(sq:int, blocks:np.uint64, a:np.uint64) -> np.uint64:
    direction_index = (7,9,-7,-9)
    legal_moves = np.uint64(0)
    for dir in direction_index:
        rank = sq // 8
        x = np.uint64(0)
        i = 1
        while x == 0 and 0 <= sq + (dir*i) < 64:
            x = blocks & np.left_shift(1, sq + (dir*i), dtype=np.uint64)
            legal_moves |= np.left_shift(1, sq + (dir*i), dtype=np.uint64)
            i += 1

    return legal_moves & a


def moves_from_blocker_config_rook(sq:int, blocks:np.uint64) -> np.uint64:
    direction_index = (8,1,-8,-1)
    legal_moves = np.uint64(0)
    for dir in direction_index:
        rank = sq // 8
        x = np.uint64(0)
        i = 1
        while x == 0 and 0 <= sq + (dir*i) < 64:
            if (dir == 1 or dir == -1) and rank != (sq + (dir*i)) // 8: # check for file owerflow 
                break
            print(sq + (dir*i))
            x = blocks & np.left_shift(1, sq + (dir*i), dtype=np.uint64)
            legal_moves |= np.left_shift(1, sq + (dir*i), dtype=np.uint64)
            i += 1

    return legal_moves

def gen_mask_edge(sq):

    rank = sq // 8
    file = sq % 8

    mask = np.uint64(0)
    mask |= np.left_shift(1, sq - (rank*8), dtype=np.uint64)
    mask |= np.left_shift(1, sq - (file), dtype=np.uint64)
    mask |= np.left_shift(1, sq + ((7 - rank)*8), dtype=np.uint64)
    mask |= np.left_shift(1, sq + (7 - file), dtype=np.uint64)
    return mask


def gen_in_between_array(sq):
    set = np.zeros(64)
    f = np.left_shift(1, sq, dtype=np.uint64)
    for target_sq in range(64):
        mask = np.left_shift(2**64 - 1, sq, dtype=np.uint64) ^ np.left_shift(2**64 - 1, target_sq, dtype=np.uint64)
        t = np.left_shift(1, target_sq, dtype=np.uint64)
        if legal_moves[3][sq] & t != 0: # can a rook reach the target_sq
            set[target_sq] = legal_moves[3][sq] & legal_moves[3][target_sq] & mask
        if legal_moves[2][sq] & t != 0: # can a bishop reach the target_sq
            set[target_sq] = legal_moves[2][sq] & legal_moves[2][target_sq] & mask

    return set


in_between = np.zeros((64,64), dtype=np.uint64)
for sq in range(64):
    in_between[sq] = gen_in_between_array(sq)

