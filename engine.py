import numpy as np
import support as sp


# board representation with bitboard

class GameState(object):
    def __init__(self) -> None:
        # starting position bitmap
        self.p = np.array([9295429630892703744, 4755801206503243776,2594073385365405696,576460752303423488,1152921504606846976,71776119061217280,129,66,36,8,16,65280], dtype=np.uint64)
        self.o = np.uint64(0)
        self.black = np.uint64(0)
        self.white = np.uint64(0)
        self.update_bb()
        self.White_to_move = True
        # concerning moves
        self.en_passant_next_move = False
        self.castle_WK = True
        self.castle_WQ = True
        self.castle_BK = True
        self.castle_BQ = True
        self.check = False
        self.checkmate = None
        # load lookup tables
        self.rook_magic_numbers = np.load('rook_magic_numbers.npy', allow_pickle=True)
        self.rook_magic_lookup = np.load('rook_magic_lookup.npy', allow_pickle=True)
        self.bishop_magic_numbers = np.load('bishop_magic_numbers.npy', allow_pickle=True)
        self.bishop_magic_lookup = np.load('bishop_magic_lookup.npy', allow_pickle=True)

    def update_bb(self):
        self.black = np.uint64(0)
        self.white = np.uint64(0)
        for b in self.p[:6]:
            self.black |= b
        for b in self.p[6:]:
            self.white |= b

        self.o = self.black | self.white

    def print_piece_bitboard(self, nr:int):
        b = self.p[nr]
        s = np.binary_repr(b, width=64)
        print(s)

    def make_move(self, move):
        '''
        changes bitboards according to move argument, put in only valid moves
        '''
        f, t = np.left_shift(1, move[0], dtype=np.uint64), np.left_shift(1, move[1], dtype=np.uint64)
        figure = self.figure_on_square(move[0])
        castl = False
        # handle castling
        if figure == 4 and self.figure_on_square(move[1]) == 0 and (move[1] == 63 or move[1] == 56): # castling black
            # comment on if statment above:
            #   the problem is that if targer sq is empty the function figure_on_square returns False (is needed of game drawing...)
            #   so I check if target sq is on of the rook starting sq, not very elegant... but should work
            castl = True
            if move[1] == 63:
                self.p[4] = np.left_shift(1, 62, dtype=np.uint64)
                self.p[0] ^= (np.left_shift(1, 63, dtype=np.uint64) | np.left_shift(1, 61, dtype=np.uint64))
            elif move[1] == 56:
                self.p[4] = np.left_shift(1, 58, dtype=np.uint64)
                self.p[0] ^= (np.left_shift(1, 56, dtype=np.uint64) | np.left_shift(1, 59, dtype=np.uint64))

        if figure == 10 and self.figure_on_square(move[1]) == 6: # castling white
            castl = True
            if move[1] == 7:
                self.p[10] = np.left_shift(1, 6, dtype=np.uint64)
                self.p[6] ^= (np.left_shift(1, 7, dtype=np.uint64) | np.left_shift(1, 5, dtype=np.uint64))
            else:
                self.p[10] = np.left_shift(1, 2, dtype=np.uint64)
                self.p[6] ^= (np.left_shift(1, 0, dtype=np.uint64) | np.left_shift(1, 3, dtype=np.uint64))

        # delete figure on target square if there was a capture
        if self.o & t != 0 and not castl:
            self.p[self.figure_on_square(move[1])] ^= t

        # delete en passant captured pawn
        if (figure == 11 or figure == 5) and move[1] % 8 != move[0] % 8 and self.o & t == 0: # conditions for en passant 
            if figure == 11:
                self.p[5] ^= np.right_shift(t, 8, dtype=np.uint64)
            if figure == 5:
                self.p[11] ^= np.left_shift(t, 8, dtype=np.uint64)
        
        # check if the next move could be en passant 
        self.en_passant_next_move = np.uint64(0)
        # white pawn double push
        if figure == 11 and move[1] - move[0] > 10:
            self.en_passant_next_move = np.left_shift(1, move[0] + 8, dtype=np.uint64)
        # black pawn
        if figure == 5 and move[0] - move[1] > 10:
            self.en_passant_next_move = np.left_shift(1, move[0] - 8, dtype=np.uint64)
            

        # upadate bitboard of moved piece
        if not castl:
            self.p[figure] ^= (f | t)

        # promoting for white
        if figure == 11 and move[1] // 8 == 7:
            self.p[11] ^= t # del the newly places pawn on target sq
            self.p[9] ^= t # add Queen on target square
        # promoting for black
        if figure == 5 and move[1] // 8 == 0:
            self.p[5] ^= t # del the newly places pawn on target sq
            self.p[3] ^= t # add Queen on target square

        # update occupied positions and change 'to_move'
        self.update_bb()
        self.White_to_move = not self.White_to_move

        self.update_castling_possibilities(move)

        # controll if there is a check after move. If so save attacks on king in self.check variable
        if figure <= 5: # black moved
            self.check = self.attacks_on_king(int(np.log2(self.p[10])), self.o, True)
        else:
            self.check = self.attacks_on_king(int(np.log2(self.p[4])), self.o, False)



        # print from where the white king in unter attack
        # sp.print_nice_bitboard(self.rook_x_ray(int(np.log2(self.p[10])), self.white))
        if self.check:
            sp.print_nice_bitboard(self.check)


    def update_castling_possibilities(self, move):
        piece = self.figure_on_square(move[1])
        white = (piece > 5)
        if white and (self.castle_WK or self.castle_WQ):
            if piece == 10:
                self.castle_WK, self.castle_WQ = False, False
            if piece == 6 and move[0] == 0:
                self.castle_WQ = False
            if piece == 6 and move[0] == 7:
                self.castle_WK = False
        elif self.castle_BK or self.castle_BQ:
            if piece == 4:
                self.castle_BK, self.castle_BQ = False, False
            if piece == 0 and move[0] == 56:
                self.castle_BQ = False
            if piece == 0 and move[0] == 63:
                self.castle_BK = False



    def check_move_validity(self, move_try):
        '''
        Check proposed move for validity, if valid make move, if not do nothing

        move_try: list with form (from, to) sq_nr

        WARNING: THIS FUNCTION WILL PROBABLY BE OBSOLETE SOON
        '''

        f, t = np.left_shift(1, move_try[0], dtype=np.uint64), np.left_shift(1, move_try[1], dtype=np.uint64)
        # sort out basic stuff
        # only move own pices
        if self.White_to_move and (self.white & f == 0):
            return
        if not self.White_to_move and (self.black & f == 0):
            return
        
        # dont capture own pieces
        if self.White_to_move and (self.white & t != 0):
            return
        if not self.White_to_move and (self.black & t != 0):
            return
        
        # implementation is shit... I have to think of something better...

        # check against computed move bitboards from some other function

        move_info = (move_try, f, t)
        self.make_move(move_info)
        print(bin(self.white))
        print(bin(self.black))



    def Generate_legal_moves(self, sq_nr):
        piece = self.figure_on_square(sq_nr)

        own_color = (piece <= 5) * self.black + (piece > 5) * self.white

        # generate bitboard of pinned pieces and prohibit movement on non in between sq
        king_sq = (piece <= 5) * int(np.log2(self.p[4])) + (piece > 5) * int(np.log2(self.p[10]))
        pinned, pinner = self.get_pinned_pieces(king_sq, own_color)

        # if the king is under attack by two pieces, the king has to move!
        if self.check & (self.check - np.uint64(1)) != 0: # check weather self.check contains multible ones
            if piece != 10 or piece != 4:
                return np.uint64(0)
        

        match piece:
            case 0 | 6:
                # rooks
                moves =  self.rook_move(sq_nr, self.o) & ~own_color
            case 1 | 7:
                # Knights
                moves =  sp.legal_moves[0][sq_nr] & ~own_color
            case 2 | 8:
                # Bishops
                moves =  self.bishop_move(sq_nr, self.o) & ~own_color
            case 3 | 9:
                # Queens
                moves =  (self.bishop_move(sq_nr, self.o) | self.rook_move(sq_nr, self.o)) & ~own_color
            case 4 | 10:
                # Kings
                castl = self.check_castling(piece)
                # keep distance to enemy king
                enemy_king_sq = (piece <= 5) * int(np.log2(self.p[10])) + (piece > 5) * int(np.log2(self.p[4]))
                moves =  (sp.legal_moves[1][sq_nr] & ~own_color & ~sp.legal_moves[1][enemy_king_sq]) | castl
                # prevent king from stepping into check
                moves_iter = moves
                while moves_iter:
                    lsb = moves_iter & -moves_iter
                    new_occ = self.o ^ (lsb | np.left_shift(1, king_sq, dtype=np.uint64))
                    attacks = self.attacks_on_king(int(np.log2(lsb)), new_occ, (piece > 5))
                    if attacks:
                        moves ^= lsb
                    moves_iter &= moves_iter - np.uint64(1)

            case 5:
                # black pawns
                moves =  self.black_pawn_move(sq_nr)
            case 11:
                # white pawns
                moves =  self.white_pawn_move(sq_nr)
            case _:
                moves = np.uint64(0)

        if np.left_shift(1, sq_nr, dtype=np.uint64) & pinned != 0: # check if relevant piece is pinned
            while pinner:
                lsb = pinner & -pinner
                if np.left_shift(1, sq_nr, dtype=np.uint64) & sp.in_between[king_sq, int(np.log2(lsb))] != 0:
                    # check if lsb is actually the pice pinning the piece that is about to move
                    moves &= (sp.in_between[king_sq, int(np.log2(lsb))] | lsb)
                pinner &= pinner - np.uint64(1)

        
        # only one check
        if self.check:
            if piece != 10 or piece != 4: # king can of course step out of the check
                # create mask of in between squares and checking piece. XOR it with moves
                check_mask = sp.in_between[king_sq, int(np.log2(self.check))] | self.check
                moves &= check_mask

        return moves
            
    def rook_move(self, sq, occ):
        mask = (sp.rank[sq // 8] | sp.file [sq % 8]) ^ np.left_shift(1, sq, dtype=np.uint64)
        blockers = (occ & mask) & ~sp.gen_mask_edge(sq) # TODO: create lookuptabel for edge mask
        index = np.right_shift((self.rook_magic_numbers[sq] * blockers), 50, dtype=np.uint64)
        attack_set = self.rook_magic_lookup[sq].get(index)
        return attack_set

    def bishop_move(self, sq, occ):
        mask = sp.legal_moves[2][sq]
        blockers = (occ & mask) & ~sp.edge_mask
        index = np.right_shift((self.bishop_magic_numbers[sq] * blockers), 53, dtype=np.uint64)
        attack_set = self.bishop_magic_lookup[sq].get(index)
        return attack_set

    def white_pawn_move(self, sq):
        pos = np.left_shift(1, sq, dtype=np.uint64)

        # Pawn pushes
        spot3 = (pos << np.uint64(8)) & ~self.o
        # check if pawn can move two squares
        spot1 = ((spot3 & sp.rank[2]) << np.uint64(8)) & ~self.o

        # Pawn captures
        spot2 = ((pos & sp.clip[0]) << np.uint64(7)) & (self.black | self.en_passant_next_move)
        spot4 = ((pos & sp.clip[-1]) << np.uint64(9)) & (self.black | self.en_passant_next_move)

        pawn_moves = spot1 | spot2 | spot3 | spot4
        return pawn_moves
    
    def white_pawn_attacks(self, sq):
        pos = np.left_shift(1, sq, dtype=np.uint64)

        # Pawn captures
        spot2 = ((pos & sp.clip[0]) << np.uint64(7)) & (self.black | self.en_passant_next_move)
        spot4 = ((pos & sp.clip[-1]) << np.uint64(9)) & (self.black | self.en_passant_next_move)

        pawn_moves = spot2 | spot4
        return pawn_moves
    
    def black_pawn_move(self, sq):
        pos = np.left_shift(1, sq, dtype=np.uint64)

        # Pawn pushes
        spot3 = (pos >> np.uint64(8)) & ~self.o
        # check if pawn can move two squares
        spot1 = ((spot3 & sp.rank[5]) >> np.uint64(8)) & ~self.o

        # Pawn captures
        spot2 = ((pos & sp.clip[0]) >> np.uint64(9)) & self.white
        spot4 = ((pos & sp.clip[-1]) >> np.uint64(7)) & self.white

        pawn_moves = spot1 | spot2 | spot3 | spot4
        return pawn_moves
    
    def black_pawn_attacks(self, sq):
        pos = np.left_shift(1, sq, dtype=np.uint64)

    
        # Pawn captures
        spot2 = ((pos & sp.clip[0]) >> np.uint64(9)) & self.white
        spot4 = ((pos & sp.clip[-1]) >> np.uint64(7)) & self.white

        pawn_moves = spot2 | spot4
        return pawn_moves
    

    def check_castling(self, piece):
        '''
        check all conditions to make sure castling is possible 

        return bitmap of possible castl positions, empty bitmap if castling is prohibited
        '''
        if piece == 10: # white king
            A, B = (self.castle_WK and sp.castl_mask[3] & self.o == 0 and self.figure_on_square(7) == 6), (self.castle_WQ and sp.castl_mask[2] & self.o == 0 and self.figure_on_square(0) == 6)
            check_Queenside = not (self.attacks_on_king(4, self.o, True) == 0 and self.attacks_on_king(2, self.o, True) == 0 and self.attacks_on_king(3, self.o, True) == 0)
            check_Kingside = not (self.attacks_on_king(5, self.o, True) == 0 and self.attacks_on_king(6, self.o, True) == 0 and self.attacks_on_king(4, self.o, True) == 0)
            
            if A and not check_Kingside:
                return np.uint64(128)
            if B and not check_Queenside:
                return np.uint64(1)
            if A and B and not (check_Queenside or check_Kingside):
                return np.uint64(1) | np.uint64(128)

        else: # black king
            A, B = (self.castle_BK and sp.castl_mask[1] & self.o == 0 and self.figure_on_square(63) == 0), (self.castle_BQ and sp.castl_mask[0] & self.o == 0 and self.figure_on_square(56) == 0)
            check_Queenside = not (self.attacks_on_king(60, self.o, False) == 0 and self.attacks_on_king(59, self.o, False) == 0 and self.attacks_on_king(58, self.o, False) == 0)
            check_Kingside = not (self.attacks_on_king(60, self.o, False) == 0 and self.attacks_on_king(61, self.o, False) == 0 and self.attacks_on_king(62, self.o, False) == 0)

            if A and not check_Kingside:
                return np.uint64(9223372036854775808)
            if B and not check_Queenside:
                return np.uint64(72057594037927936)
            if A and B and not (check_Kingside or check_Queenside):
                return np.uint64(9223372036854775808) | np.uint64(72057594037927936)
        
        return np.uint64(0)
    

    def attacks_on_king(self, king_sq, occ, color_white:bool):
        '''
        return bitboard of all positions the king is attacked 

        to do this we pretend there is a super-piece on the sq of the king, then AND it with the according opposite color bitboards
        Queens are treated as bishops as well as rooks
        '''
        color_key = (not color_white) * [6,7,8,9,10,11] +  (color_white) * [0,1,2,3,4,5] # choose right indices for color
        pawn_attacks = (color_white * self.white_pawn_attacks(king_sq) + (not color_white) * self.black_pawn_attacks(king_sq)) & self.p[color_key[5]]
        knight_attacks = sp.legal_moves[0][king_sq] & self.p[color_key[1]]
        bishop_attacks = self.bishop_move(king_sq, occ) & (self.p[color_key[2]] | self.p[color_key[3]])
        rook_attacks = self.rook_move(king_sq, occ) & (self.p[color_key[0]] | self.p[color_key[3]])

        return pawn_attacks | knight_attacks | bishop_attacks | rook_attacks

    def rook_x_ray(self, sq, blocks):
        '''
        return bitboard of not directly attacked pieces, but those who stand on a attacked line behind other pieces 
        '''

        attacks = self.rook_move(sq, self.o)
        blocks &= attacks
        return attacks ^ self.rook_move(sq, (self.o ^ blocks))


    def bishop_x_ray(self, sq, blocks):

        attacks = self.bishop_move(sq, self.o)
        blocks &= attacks
        return attacks ^ self.bishop_move(sq, (self.o ^ blocks))
    

    def get_pinned_pieces(self, king_sq, own_color):
        '''
        return bb with all the pinned pieces of own color
        
        it probably would be smart to save from where the piece is pinned
        '''
        if (self.black & own_color != 0): # opposite color RQ and BQ
            RQ = self.p[6] | self.p[9]
            BQ = self.p[8] | self.p[9]
        else:
            RQ = self.p[0] | self.p[3]
            BQ = self.p[2] | self.p[3]

        pinned = np.uint64(0)
        # pretend the is a rook/bishop on the king square
        pinner = (self.rook_x_ray(king_sq, own_color) & RQ) | (self.bishop_x_ray(king_sq, own_color) & BQ)
        while pinner: # extract the single pinners postition and determine the pinned pieces position
            lsb = pinner & -pinner
            pinned |= sp.in_between[int(np.log2(lsb)), king_sq] & own_color
            pinner &= pinner - np.uint64(1)

        pinner = (self.rook_x_ray(king_sq, own_color) & RQ) | (self.bishop_x_ray(king_sq, own_color) & BQ)

        return pinned, pinner




    

    def figure_on_square(self, sq_nr):
        '''
        this methode returns the index of the bitboard of the piece on sqnr
        '''
        s = np.left_shift(1, sq_nr, dtype=np.uint64)
        for i,b in enumerate(self.p):
            if s & b != 0:
                return i
        return False
            
if __name__ == '__main__':
    state = GameState()
