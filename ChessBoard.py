import numpy as np
from typing import Tuple, List
from copy import deepcopy
import time


class Piece:
    """
    Class to Represent Chess Piece
    with Team, Piece Type and Initial Position
    """
    def __init__(self, team: str, p_type: str, i_pos: Tuple[int, int], r_id = None):
        self.team = team
        self.p_type = p_type
        self.journey = [i_pos]
        if r_id is None:
            self.id = team + " " + p_type + " " + str(i_pos[1])
        else:
            self.id = r_id

    def is_start(self):
        """
        Function to know if a Piece is at its Initial Position
        """
        return True if len(self.journey) == 1 else False

    def new_pos(self, pos: Tuple[int, int]):
        """
        Function to Record, Every new Step
        """
        self.journey.append(pos)

    def __repr__(self):
        return f"{self.team}: {self.p_type}"


class Block:
    """
    Class to represent 1 out of 64 blocks on the Board
    with Piece object
    """
    def __init__(self, comp: str | Piece):
        if isinstance(comp, str):
            self.name = comp
            self.piece = None
        else:
            self.piece = comp 
            self.name = comp.team + comp.p_type

    def __repr__(self):
        if self.name != " ":
            return f"{self.piece.team}-{self.piece.p_type}"
        else:
            return self.name
     

class ChessBoard:
    """
    Class to represent Chess Board
    """
    def __init__(self):
        self.board = np.empty((8, 8), dtype=object)
        self.snap_shots = []
        self.all_pos_snaps = []
        self.is_b_on_check, self.is_w_on_check = False, False
        self.operator = False
        for y in range(8):
            self.board[1, y] = Block(Piece("W", "PA", (1, y)))
            self.board[6, y] = Block(Piece("B", "PA", (6, y)))
        for y in (0, 7):
            self.board[0, y] = Block(Piece("W", "RO", (0, y)))
            self.board[7, y] = Block(Piece("B", "RO", (0, y)))
        for y in (1, 6):
            self.board[0, y] = Block(Piece("W", "KN", (0, y)))
            self.board[7, y] = Block(Piece("B", "KN", (7, y)))
        for y in (2, 5):
            self.board[0, y] = Block(Piece("W", "BI", (0, y)))
            self.board[7, y] = Block(Piece("B", "BI", (0, y)))
        self.board[0, 3] = Block(Piece("W", "QU", (0, 3)))
        self.board[0, 4] = Block(Piece("W", "KI", (0, 4)))
        self.board[7, 3] = Block(Piece("B", "QU", (7, 3)))
        self.board[7, 4] = Block(Piece("B", "KI", (7, 4)))

        for x in range(2, 6):
            for y in range(0, 8):
                self.board[x, y] = Block(" ")

        # Keeping track of all Positions
        self.all_pos, self.team_wise_id = dict(), list()
        temp = []
        for x in [0, 1, 6, 7]:
            for y in range(8):
                block = self.board[x, y]
                temp.append(block.piece.id)
                self.all_pos[block.piece.id] = (x, y)
            if x in [1, 7]:
                self.team_wise_id.append(temp)
                temp = []

    def move(self, i_pos: Tuple[int, int], n_pos: Tuple[int, int], is_record: bool = False, p_conv = "None"):
        """
        Function to move a Piece on the Board
        with Current and New Positions
        """
        if is_record or self.is_b_on_check or self.is_w_on_check:
            self.snap_shot()
            if self.is_b_on_check or self.is_w_on_check:
                self.operator = True
        curr_block, new_block = self.board[i_pos[0], i_pos[1]], self.board[n_pos[0], n_pos[1]]

        # Castling Operation
        if curr_block.piece.p_type == "KI" and (new_block.piece is not None and new_block.name in ["BRO", "WRO"]) and curr_block.piece.team == new_block.piece.team:
            if (curr_block.piece.team == "W" and not self.is_w_on_check) or (curr_block.piece.team == "B" and not self.is_b_on_check):
                if n_pos[1] > i_pos[1]:
                    self.move(i_pos, (i_pos[0], i_pos[1] + 2))
                    self.move(n_pos, (n_pos[0], n_pos[1] - 2))
                else:
                    self.move(i_pos, (i_pos[0], i_pos[1] - 2))
                    self.move(n_pos, (n_pos[0], n_pos[1] + 3))
        else:
            self.all_pos[curr_block.piece.id] = n_pos
            if new_block.piece is not None:
                self.all_pos[new_block.piece.id] = "DEAD"

            if not is_record:
                curr_block.piece.new_pos(n_pos)
            new_block.piece = curr_block.piece
            new_block.name = curr_block.name
            curr_block.name = " "
            curr_block.piece = None
            # Pawn Conversion when reaching Opposite End!
            if new_block.piece.p_type == "PA" and n_pos[0] in {0, 7}:
                if p_conv is None:
                    p_conv = "QU"
                r_id = new_block.piece.team + " " + p_conv + " " + str(time.time())
                new_block.piece = Piece(new_block.piece.team, p_conv, n_pos, r_id)
                new_block.name = new_block.piece.team + new_block.piece.p_type
                self.all_pos[r_id] = n_pos
                if new_block.piece.team == "W":
                    self.team_wise_id[0].append(r_id)
                else:
                    self.team_wise_id[1].append(r_id)

            # For Check
            if not is_record:
                new_mask = Prediction(self).trace_path(n_pos)
                if self.board[n_pos[0], n_pos[1]].piece.team == "W":
                    if self.all_pos["B KI 4"] in new_mask:
                        # freeze all Blacks
                        self.is_b_on_check = True
                        # Checking for Mate
                        if self.is_mate("B", n_pos):
                            #print("Check Mate")
                            pass
                        # New adds to make self.operate as false even though if it's True
                        self.operator = False
                else:
                    if self.all_pos["W KI 4"] in new_mask:
                        # freeze all whites
                        # not working from here
                        self.operator = False
                        self.is_w_on_check = True
                        if self.is_mate("W", n_pos):
                            #print("Check Mate")
                            pass

        if self.operator:
            if self.is_under_attack():
                if not is_record:
                    self.prev_cp()
            else:
                if not is_record:
                    self.snap_shots, self.all_pos_snaps = [], []
                    if self.is_b_on_check:
                        self.is_b_on_check = False
                    if self.is_w_on_check:
                        self.is_w_on_check = False
            self.operator = False

    def is_under_attack(self):
        """
        Function to check if king is under attack after moving a piece
        """
        p = Prediction(self)
        cap_piece, check = (self.all_pos["B KI 4"], 0) if self.is_b_on_check else (self.all_pos["W KI 4"], 1)
        for key in self.team_wise_id[check]:
            if "KI" in key.split():
                # For King Piece we have spl validation to check the safety of the Piece
                # So we don't have to do it again.
                continue
            if self.all_pos[key] != "DEAD" and cap_piece in p.trace_path(self.all_pos[key]):
                return True
        return False

    def is_mate(self, team: str, a_piece_pos: Tuple[int, int]):
        """
        Function to check for the Mate
        """
        p = Prediction(self)
        # Checking to Move the King Piece
        if len(p.trace_path(self.all_pos[team + " KI 4"])) != 0:
            return False
        else:
            # Checking to Remove the attacking Piece
            for i in self.team_wise_id[0 if team == "W" else 1]:
                if self.all_pos[i] != "DEAD":
                    if a_piece_pos in p.trace_path(self.all_pos[i]):
                        return False
            # Checking to Block the Way
            if self.board[a_piece_pos[0], a_piece_pos[1]].piece.p_type == "KN":
                return True
            a_piece_mask = p.trace_path(a_piece_pos)
            z = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
            for i in z:
                m1 = self.all_pos[team + " KI 4"] + i
                if m1 in a_piece_mask:
                    break
            for i in self.team_wise_id[0 if team == "W" else 1]:
                if self.all_pos[i] != "DEAD":
                    if m1 in p.trace_path(self.all_pos[i]):
                        return False
            return True

    def snap_shot(self):
        """
        Function to record Past Snapshots
        For checking the King's Safe Position
        """
        temp = deepcopy(self.board)
        self.snap_shots.append(temp)
        self.all_pos_snaps.append(deepcopy(self.all_pos))

    def prev_cp(self):
        """
        Function to restore to previous snapshot
        """
        self.board = deepcopy(self.snap_shots.pop())
        self.all_pos = deepcopy(self.all_pos_snaps.pop())

    def get_board(self):
        return self.all_pos

    def robo_move(self, i_pos: Tuple[int, int], n_pos: Tuple[int, int], p_conv = "None"):
        """
        Function to move a Piece on the Board
        with Current and New Positions
        """
        curr_block, new_block = self.board[i_pos[0], i_pos[1]], self.board[n_pos[0], n_pos[1]]

        # Castling Operation
        if curr_block.piece.p_type == "KI" and (new_block.piece is not None and new_block.name in ["BRO", "WRO"]) and curr_block.piece.team == new_block.piece.team:
            if (curr_block.piece.team == "W" and not self.is_w_on_check) or (curr_block.piece.team == "B" and not self.is_b_on_check):
                if n_pos[1] > i_pos[1]:
                    self.move(i_pos, (i_pos[0], i_pos[1] + 2))
                    self.move(n_pos, (n_pos[0], n_pos[1] - 2))
                else:
                    self.move(i_pos, (i_pos[0], i_pos[1] - 2))
                    self.move(n_pos, (n_pos[0], n_pos[1] + 3))
        else:
            self.all_pos[curr_block.piece.id] = n_pos
            if new_block.piece is not None:
                self.all_pos[new_block.piece.id] = "DEAD"

            curr_block.piece.new_pos(n_pos)
            new_block.piece = curr_block.piece
            new_block.name = curr_block.name
            curr_block.name = " "
            curr_block.piece = None
            # Pawn Conversion when reaching Opposite End!
            if new_block.piece.p_type == "PA" and n_pos[0] in {0, 7}:
                if p_conv is None:
                    p_conv = "QU"
                r_id = new_block.piece.team + " " + p_conv + " " + str(time.time())
                new_block.piece = Piece(new_block.piece.team, p_conv, n_pos, r_id)
                new_block.name = new_block.piece.team + new_block.piece.p_type
                self.all_pos[r_id] = n_pos
                if new_block.piece.team == "W":
                    self.team_wise_id[0].append(r_id)
                else:
                    self.team_wise_id[1].append(r_id)


    def __repr__(self):
        for x in range(0, 8):
            for y in range(0, 8):
                print(self.board[x, y], end="\t")
            print()
        return ''


class Prediction:
    """
    Class to predict Moves of a Piece
    with Board obj
    """
    def __init__(self, board: ChessBoard):
        self.board = board

    def is_end(self, i_pos: Tuple[int, int], n_pos: Tuple[int, int]):
        """
        Function to determine if a point is End Point or not in the Trajectory
        with Current and New Positions
        """
        if n_pos[0] < 0 or n_pos[0] >= 8 or n_pos[1] < 0 or n_pos[1] >= 8:
            return 0  # Stop here if out of bounds
        curr_block, new_block = self.board.board[i_pos[0], i_pos[1]], self.board.board[n_pos[0], n_pos[1]]
        if new_block.piece is None:
            return 2  # Continue otherwise
        if curr_block.piece.team == new_block.piece.team:
            return 0  # Stop here if the destination block is the same team
        elif curr_block.piece.team != new_block.piece.team:
            return 1  # Add this and Stop if the destination block is an opponent piece
        else:
            return 2  # Continue otherwise

    def trace_path(self, pos: Tuple[int, int]):
        """
        Function to predict all possible moves of a Piece
        with Current Position of the Piece
        """
        curr_block = self.board.board[pos[0], pos[1]]
        piece = curr_block.piece
        mask = []
        match piece.p_type:
            case "PA":
                if piece.team == "W":
                    # White Pawn moves
                    directions = [(1, 0), (1, 1), (1, -1)]
                    if piece.is_start:
                        directions.append((2, 0))  # Initial double move
                else:
                    # Black Pawn moves
                    directions = [(-1, 0), (-1, 1), (-1, -1)]
                    if piece.is_start:
                        directions.append((-2, 0))  # Initial double move
                
                front_step = False
                for d in directions:
                    n_pos = (pos[0] + d[0], pos[1] + d[1])
                    result = self.is_end(pos, n_pos)
                    if directions.index(d) == 0 and result == 2:
                        front_step = True
                    if (result == 2 and directions.index(d) == 0) or (result == 1 and (directions.index(d) in {1, 2})):
                        mask.append(n_pos)
                    if result == 2 and (directions.index(d) == 3 and front_step):
                        if piece.is_start():
                            mask.append(n_pos)
            case "RO":
                for d in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    n_pos = pos
                    while True:
                        n_pos = (n_pos[0] + d[0], n_pos[1] + d[1])
                        result = self.is_end(pos, n_pos)
                        if result == 0:
                            break
                        mask.append(n_pos)
                        if result == 1:
                            break
            case "KN":
                moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
                for d in moves:
                    n_pos = (pos[0] + d[0], pos[1] + d[1])
                    result = self.is_end(pos, n_pos)
                    if result != 0:
                        mask.append(n_pos)
            case "BI":
                for d in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    n_pos = pos
                    while True:
                        n_pos = (n_pos[0] + d[0], n_pos[1] + d[1])
                        result = self.is_end(pos, n_pos)
                        if result == 0:
                            break
                        mask.append(n_pos)
                        if result == 1:
                            break
            case "QU":
                for d in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    n_pos = pos
                    while True:
                        n_pos = (n_pos[0] + d[0], n_pos[1] + d[1])
                        result = self.is_end(pos, n_pos)
                        if result == 0:
                            break
                        mask.append(n_pos)
                        if result == 1:
                            break
            case "KI":
                moves = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                # Checking for castling rule
                if piece.team == "W" and piece.is_start():
                    for key in self.board.team_wise_id[0]:
                        if 'RO' in key.split() and self.board.all_pos[key] != "DEAD" and self.board.board[self.board.all_pos[key]].piece.is_start():
                            bi_pos = int(key.split()[2])
                            temp = 0
                            if bi_pos < pos[1]:
                                for y in range(bi_pos + 1, pos[1]):
                                    if self.board.board[pos[0], y].piece is None:
                                        temp += 1
                                if temp == 2:
                                    moves.append((0, -2))
                            else:
                                for y in range(pos[1] + 1, bi_pos):
                                    if self.board.board[pos[0], y].piece is None:
                                        temp += 1
                                if temp == 3:
                                    moves.append((0, 2))
                if piece.team == "B" and piece.is_start():
                    for key in self.board.team_wise_id[1]:
                        if 'RO' in key.split() and self.board.all_pos[key] != "DEAD" and self.board.board[self.board.all_pos[key]].piece.is_start():
                            bi_pos = int(key.split()[2])
                            temp = 0
                            if bi_pos < pos[1]:
                                for y in range(bi_pos + 1, pos[1]):
                                    if self.board.board[pos[0], y].piece is None:
                                        temp += 1
                                if temp == 2:
                                    moves.append((0, -2))
                            else:
                                for y in range(pos[1] + 1, bi_pos):
                                    if self.board.board[pos[0], y].piece is None:
                                        temp += 1
                                if temp == 3:
                                    moves.append((0, 2))

                for d in moves:
                    n_pos = (pos[0] + d[0], pos[1] + d[1])
                    result = self.is_end(pos, n_pos)
                    if result != 0:
                        self.board.move(pos, n_pos, True)
                        count = 0
                        if piece.team == "W":
                            for key in self.board.team_wise_id[1]:
                                if self.board.all_pos[key] == "DEAD":
                                    count += 1
                                elif key == "B KI 4":
                                    dis = abs(n_pos[0] - self.board.all_pos[key][0]) + abs(n_pos[1] - self.board.all_pos[key][1])
                                    if dis > 1:
                                        count += 1
                                elif n_pos not in self.trace_path(self.board.all_pos[key]):
                                    count += 1
                                if count == 16:
                                    if d == (0, 2):
                                        mask.append((n_pos[0], n_pos[1] + 2))
                                    elif d == (0, -2):
                                        mask.append((n_pos[0], n_pos[1] - 1))
                                    else:
                                        mask.append(n_pos)
                        else:
                            for key in self.board.team_wise_id[0]:
                                if self.board.all_pos[key] == "DEAD":
                                    count += 1
                                elif key == "W KI 4":
                                    dis = abs(n_pos[0] - self.board.all_pos[key][0]) + abs(n_pos[1] - self.board.all_pos[key][1])
                                    if dis > 1:
                                        count += 1
                                elif n_pos not in self.trace_path(self.board.all_pos[key]):
                                    count += 1
                                if count == 16:
                                    if d == (0, 2):
                                        mask.append((n_pos[0], n_pos[1] + 2))
                                    elif d == (0, -2):
                                        mask.append((n_pos[0], n_pos[1] - 1))
                                    else:
                                        mask.append(n_pos)
                        self.board.prev_cp()

        return mask
    
    def print_traj(self, pos: Tuple[int, int]):
        """
        Function to Visualize the Trajectory
        with Current Position
        """
        mask = self.trace_path(pos)
        for x in range(0, 8):
            for y in range(0, 8):
                if (x, y) == pos:
                    print("|@$|", end="\t")
                elif (x, y) not in mask:
                    print(self.board.board[x, y], end="\t")
                else:
                    print("*", end="\t")
            print()
