import support as sp
import numpy as np

rook = np.load('rook.npy')
rook_blocks = np.load('rook_blocks.npy')
bishop = np.load('bishop.npy')
bishop_blocks = np.load('bishop_blocks.npy')
imax = 0

def generate_magic_number(sq:int):
    # n = 10
    # sq_on_edge = (sq // 8 == 0 or sq // 8 == 8 or sq % 8 == 0 or sq % 8 == 8)
    # if sq_on_edge:
    #     n = 12
    n = 14

    magic_found = False
    M = 0
    ind = 0
    # counter = 0

    while not magic_found:
        M = np.random.randint(2**64, dtype=np.uint64)
        ind = candidate_magic_number(sq, M, n)
        if ind != False:
            magic_found = True
        # counter += 1
        # if counter % 100 == 0:
        #     print(counter)
        #     print(imax / (2**14))

    return M, ind

def candidate_magic_number(sq, M:np.uint64, n):
    global imax
    
    indices = dict()
    for i in range(2**14):
        if rook_blocks[sq][i] & gen_mask_edge_rook(sq) == 0:
            index = np.right_shift((M * rook_blocks[sq][i]), 64-n, dtype=np.uint64)
            if index in indices.keys():
                if rook[sq][i] == rook[sq][indices.get(index)]:
                    continue
                else:
                    if i > imax:
                        imax = i
                    return False
            else:
                indices.update({index:i})

    return indices

def gen_mask_edge_rook(sq):

    rank = sq // 8
    file = sq % 8

    mask = np.uint64(0)
    mask |= np.left_shift(1, sq - (rank*8), dtype=np.uint64)
    mask |= np.left_shift(1, sq - (file), dtype=np.uint64)
    mask |= np.left_shift(1, sq + ((7 - rank)*8), dtype=np.uint64)
    mask |= np.left_shift(1, sq + (7 - file), dtype=np.uint64)
    return mask



def save_rook_magic():
    rook_magic_lookup = []
    rook_magic_numbers = []
    for sq in range(64):
        M, ind = generate_magic_number(sq)
        for index in ind.keys():  # type: ignore
            attack_set = rook[sq][ind.get(index)] # type: ignore
            ind.update({index:attack_set}) # type: ignore

        rook_magic_numbers.append(M)
        rook_magic_lookup.append(ind)
        print(f'progress: {sq+1}/64')

    np.save('rook_magic_lookup.npy', np.array(rook_magic_lookup), allow_pickle=True)
    np.save('rook_magic_numbers.npy', np.array(rook_magic_numbers), allow_pickle=True)



