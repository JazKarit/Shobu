from re import S
from sre_constants import SUCCESS
from turtle import pos
import numpy as np
import random
import itertools
import copy

class Board:

    def __init__(self):
        self.stones = [set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])]

class Game:

    def __init__(self,boards = [Board(),Board(),Board(),Board()]):
        self.last_passive = None
        self.last_aggressive = None
        self.boards = boards
        self.letter_to_col = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
        self.user_player = 0
        self.ai_player = 1

    def play_game(self):
        while True:
            #self.get_ai_random_move()
            self.depth_n_ai(2)
            self.print_game()
            self.get_user_move()
            self.print_game()
            

    def get_ai_random_move(self):

        passive_move, aggressive_move = random.choice(list(self.get_available_moves(self.ai_player)[0]))
        
        self.last_passive = passive_move
        self.last_aggressive = (aggressive_move[0], aggressive_move[1][0], aggressive_move[2], aggressive_move[1][1])

        self.boards[passive_move[0]].stones[self.ai_player].remove(passive_move[1])
        self.boards[passive_move[0]].stones[self.ai_player].add(passive_move[2])
        
        

        self.boards[aggressive_move[0]].stones[self.ai_player].remove(aggressive_move[1][0])
        self.boards[aggressive_move[0]].stones[self.ai_player].add(aggressive_move[1][1])
        if aggressive_move[2]:
            pushed_stone_start_coord = aggressive_move[2][0]
            pushed_stone_end_coord = aggressive_move[2][1]
            self.boards[aggressive_move[0]].stones[self.user_player].remove(pushed_stone_start_coord)
            if pushed_stone_end_coord:
                self.boards[aggressive_move[0]].stones[self.user_player].add(pushed_stone_end_coord)
    
    # def get_boards_as_array(self):
    #     boards = np.empty(5)
    #     boards[:] = np.nan

    #     for board_num in range(4):
    #         for player in range(2):
    #             player_board_stones = list(self.boards[board_num].stones[player])
    #             for stone_coord in range(len(player_board_stones)):
    #                 for coordinate in range(2):
    #                     boards[board_num][player][stone_coord][coordinate] = player_board_stones[stone_coord][coordinate]
    #     return boards

    def get_available_moves_using_array(self,player,boards):
        passive_moves = self.get_available_passive_moves_using_array(player)
        aggressive_moves = self.get_available_aggressive_moves_using_array(player)
        passive_dict = {}
        aggressive_dict = {}
        for board_num in range(4):
            board_moves = passive_moves[board_num]
            if board_moves:
                for start_coord, moves in board_moves.items():
                    for move in moves:
                        end_coord = move[0]
                        heading = move[1]
                        if heading not in passive_dict.keys():
                            passive_dict[heading] = set()
                        passive_dict[heading].add((board_num,start_coord,end_coord))
        for board_num in range(4):
            board_moves = aggressive_moves[board_num]
            if board_moves:
                for start_coord, moves in board_moves.items():
                    for move in moves:
                        end_coord = move[0]
                        push = move[1]
                        heading = move[2]
                        if heading not in aggressive_dict.keys():
                            aggressive_dict[heading] = set()
                        aggressive_dict[heading].add((board_num,(start_coord,end_coord),push))
        moves = set()
        passive_left_headings = 0
        passive_right_headings = 0
        for heading, passive_moves in passive_dict.items():
            aggressive_moves = aggressive_dict[heading]
            passive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, passive_moves))
            passive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, passive_moves))
            aggressive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, aggressive_moves))
            aggressive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, aggressive_moves))
            left_right_moves = itertools.product(passive_left_moves,aggressive_right_moves)
            right_left_moves = itertools.product(passive_right_moves,aggressive_left_moves)
            moves = moves.union(set(left_right_moves)).union(set(right_left_moves))
            if len(passive_left_moves) > 0:
                passive_left_headings += 1
            if len(passive_right_moves) > 0:
                passive_right_headings += 1
                
        return (moves, (passive_left_headings, passive_right_headings))

    def board_evalutation(self,n,board):
        self.get_available_aggressive_moves()

    def depth_n_ai(self,n):

        if n == 0:
            return

        best_eval = -1
        best_move = None
        i = 0
        moves = self.get_available_moves(self.ai_player)[0]
        evals = np.zeros(len(moves))
        for move_num in range(len(moves)):
            # if n ==2:
            #     i+=1
            #     print(i)
            passive, aggressive = moves[move_num]
            possible_game = copy.deepcopy(self)
            possible_game.boards[passive[0]].stones[self.ai_player].remove(passive[1])
            possible_game.boards[passive[0]].stones[self.ai_player].add(passive[2])
            possible_game.boards[aggressive[0]].stones[self.ai_player].remove(aggressive[1][0])
            possible_game.boards[aggressive[0]].stones[self.ai_player].add(aggressive[1][1])
            if aggressive[2]:
                pushed_stone_start_coord = aggressive[2][0]
                pushed_stone_end_coord = aggressive[2][1]
                possible_game.boards[aggressive[0]].stones[self.user_player].remove(pushed_stone_start_coord)
                if pushed_stone_end_coord:
                    possible_game.boards[aggressive[0]].stones[self.user_player].add(pushed_stone_end_coord)
            possible_eval = possible_game.evaluation(self.ai_player)
            evals[move_num] = possible_eval
        print(np.where(evals == np.max(evals))[0][0])
        best_move = moves[np.where(evals == np.max(evals))[0][0]]

        # get indexes for top 10% of evals
        # iterate depth
        # for move with eval > 90%:
        #    eval 2
        
        passive_move, aggressive_move = best_move

        self.last_passive = passive_move
        self.last_aggressive = (aggressive_move[0], aggressive_move[1][0], aggressive_move[2], aggressive_move[1][1])

        self.boards[passive_move[0]].stones[self.ai_player].remove(passive_move[1])
        self.boards[passive_move[0]].stones[self.ai_player].add(passive_move[2])
        
        

        self.boards[aggressive_move[0]].stones[self.ai_player].remove(aggressive_move[1][0])
        self.boards[aggressive_move[0]].stones[self.ai_player].add(aggressive_move[1][1])
        if aggressive_move[2]:
            pushed_stone_start_coord = aggressive_move[2][0]
            pushed_stone_end_coord = aggressive_move[2][1]
            self.boards[aggressive_move[0]].stones[self.user_player].remove(pushed_stone_start_coord)
            if pushed_stone_end_coord:
                self.boards[aggressive_move[0]].stones[self.user_player].add(pushed_stone_end_coord)
    
    def evaluation(self, player):
        enemy = (player + 1) % 2
        move_fraction = (self.get_available_moves(player)[1][0] + self.get_available_moves(player)[1][1]) / (self.get_available_moves(enemy)[1][0] + self.get_available_moves(enemy)[1][1])
        num_moves_evaluation = move_fraction - 0.5
        my_stones_board = [0, 0, 0, 0]
        enemy_stones_board = [0, 0, 0, 0]
        importance_board = [0, 0, 0, 0]
        eval_board = [0, 0, 0, 0]
        for board_num in range(4):
            my_stones_board[board_num] = len(self.boards[board_num].stones[player])
            enemy_stones_board[board_num] = len(self.boards[board_num].stones[enemy])
            if my_stones_board[board_num] == 0:
                return 0
            elif enemy_stones_board[board_num] == 0:
                return 1
            max_stones = max(my_stones_board[board_num], enemy_stones_board[board_num])
            min_stones = min(my_stones_board[board_num], enemy_stones_board[board_num])
            sum_stones = my_stones_board[board_num] + enemy_stones_board[board_num]
            importance_board[board_num] = max_stones / (4 * min_stones ** 2)
            eval_board[board_num] = my_stones_board[board_num] / sum_stones
        sum_importances = sum(importance_board)
        num_stones_evaluation = np.dot(eval_board, importance_board) / sum_importances
        return 2 * ( 0.7 * num_stones_evaluation + 0.3 * num_moves_evaluation - 0.5)

    def get_user_move(self):
        success = False

        while not success:
            self.last_passive = None
            self.last_aggressive = None
            passive = None
            valid_passive = False
            while not passive or not valid_passive:
                passive_move_user = input("Passive Move: ")
                passive = self.convert_move_to_computer(passive_move_user)
                if not passive:
                    print("Passive move must stay on the same board")
                else:
                    valid_passive = self.try_passive_move(self.user_player,passive[0],passive[1],passive[2])
            self.last_passive = passive
            print()
            self.print_game()
            
            required_aggressive_boards = [0,2]
            if passive[0] % 2 == 0:
                required_aggressive_boards = [1,3]
        
            try_aggressive_again = True
            while try_aggressive_again:
                aggressive_move_user = input("Aggressive Move: ")
                aggressive = self.convert_move_to_computer(aggressive_move_user)
                if not aggressive:
                    print("Aggressive move must stay on the same board")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(self.user_player,passive[0],passive[2],passive[1])
                    continue
                if aggressive[0] not in required_aggressive_boards:
                    print("Aggressive move must happen on a board on the opposite side")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(self.user_player,passive[0],passive[2],passive[1])
                    continue
                if passive[2][0] - passive[1][0] != aggressive[2][0] - aggressive[1][0] or passive[2][1] - passive[1][1] != aggressive[2][1] - aggressive[1][1]:
                    print("Passive move and aggressive move do not match")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(self.user_player,passive[0],passive[2],passive[1])
                    continue
                valid_aggressive = self.try_aggressive_move(self.user_player,aggressive[0],aggressive[1],aggressive[2])
                if valid_aggressive:
                    try_aggressive_again = False
                    success = True
                    self.last_aggressive = aggressive
                    print()
                else:
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(self.user_player,passive[0],passive[2],passive[1])


    def get_homeboards(self,player):
        if player == 0:
            return [2,3]
        else:
            return [0,1]

    def convert_move_to_computer(self, move):
        move = move.replace(' ','')
        try:
            start_coord_x = self.letter_to_col[move[0]]
            end_coord_x = self.letter_to_col[move[2]]
            start_coord_y = 8 - int(move[1])
            end_coord_y = 8 - int(move[3])
        except:
            return False
        board_num = 0
        if start_coord_x >= 4:
            if end_coord_x >= 4:
                board_num += 1
                start_coord_x -= 4
                end_coord_x -= 4
            else:
                return False
        if start_coord_y >= 4:
            if end_coord_y >= 4:
                board_num += 2
                start_coord_y -= 4
                end_coord_y -= 4
            else:
                return False
        return (board_num, (start_coord_y,start_coord_x), (end_coord_y,end_coord_x))

    def try_move(self,player,passive,aggresive):
        success = self.try_passive_move(player,passive[0],passive[1],passive[2])
        if not success:
            return False
        required_aggressive_boards = [0,2]
        if passive[0] % 2 == 0:
            required_aggressive_boards = [1,3]

        if aggresive[0] not in required_aggressive_boards:
            print("Aggressive Move must happen on a board on the opposite side")
            self.try_passive_move(player,passive[0],passive[2],passive[1])
            return False
        if passive[2][0] - passive[1][0] != aggresive[2][0] - aggresive[1][0] or passive[2][1] - passive[1][1] != aggresive[2][1] - aggresive[1][1]:
            print("Passive move and aggressive move do not match")
            self.try_passive_move(player,passive[0],passive[2],passive[1])
            return False
        success = self.try_aggressive_move(player,aggresive[0],aggresive[1],aggresive[2])
        if not success:
            self.try_passive_move(player,passive[0],passive[2],passive[1])
            return False
        return True

    def try_passive_move(self,player,board,start_coord,end_coord):
        available_passive_moves = self.get_available_passive_moves(player)[board]

        if available_passive_moves and start_coord in available_passive_moves and end_coord in list(zip(*available_passive_moves[start_coord]))[0]:
            self.boards[board].stones[player].remove(start_coord)
            self.boards[board].stones[player].add(end_coord)
            return True
        else:
            print("Invalid passive move")
            return False
    
    def try_aggressive_move(self,player,board,start_coord,end_coord):
        available_aggressive_moves = self.get_available_aggressive_moves(player)[board]
        if available_aggressive_moves and start_coord in available_aggressive_moves:
            for move in available_aggressive_moves[start_coord]:
                if move[0] == end_coord:
                    self.boards[board].stones[player].remove(start_coord)
                    self.boards[board].stones[player].add(end_coord)
                    if move[1]:
                        pushed_stone_start_coord = move[1][0]
                        pushed_stone_end_coord = move[1][1]
                        self.boards[board].stones[(player+1)%2].remove(pushed_stone_start_coord)
                        if pushed_stone_end_coord:
                            self.boards[board].stones[(player+1)%2].add(pushed_stone_end_coord)
                    return True
        print("Invalid aggressive move")
        return False

    
    def print_game(self):

        def get_board_row_string(board_num, row):
            row_print = ''
            for col in range(4):
                if (row, col) in self.boards[board_num].stones[0]:
                    row_print += 'x '
                elif (row, col) in self.boards[board_num].stones[1]:
                    row_print += 'o '
                elif (self.last_aggressive and board_num == self.last_aggressive[0] and (row, col) == self.last_aggressive[1]) or (self.last_passive and board_num == self.last_passive[0] and (row, col) == self.last_passive[1]):
                    row_print += '. '
                else:
                    row_print += '  '
            return row_print

        print('  + - - - - +    + - - - - +')
        row_num = 8
        for row in range(4):
            row_print = str(row_num) + ' | '
            row_num -= 1
            row_print += get_board_row_string(0,row)
            row_print += '|    | '
            row_print += get_board_row_string(1,row)
            row_print += '|'
            print(row_print)
        print('  + - - - - +    + - - - - +')
        print('    a b c d        e f g h')
        print('  + - - - - +    + - - - - +')
        for row in range(4):
            row_print = str(row_num) + ' | '
            row_num -= 1
            row_print += get_board_row_string(2,row)
            row_print += '|    | '
            row_print += get_board_row_string(3,row)
            row_print += '|'
            print(row_print)
        print('  + - - - - +    + - - - - +')
        print('    a b c d        e f g h')
        print()
        print("Current Evaluation: " + str(self.evaluation(self.user_player)))
        print()
        
    def get_available_moves(self, player):
        passive_moves = self.get_available_passive_moves(player)
        aggressive_moves = self.get_available_aggressive_moves(player)
        passive_dict = {}
        aggressive_dict = {}
        for board_num in range(4):
            board_moves = passive_moves[board_num]
            if board_moves:
                for start_coord, moves in board_moves.items():
                    for move in moves:
                        end_coord = move[0]
                        heading = move[1]
                        if heading not in passive_dict.keys():
                            passive_dict[heading] = set()
                        passive_dict[heading].add((board_num,start_coord,end_coord))
        for board_num in range(4):
            board_moves = aggressive_moves[board_num]
            if board_moves:
                for start_coord, moves in board_moves.items():
                    for move in moves:
                        end_coord = move[0]
                        push = move[1]
                        heading = move[2]
                        if heading not in aggressive_dict.keys():
                            aggressive_dict[heading] = set()
                        aggressive_dict[heading].add((board_num,(start_coord,end_coord),push))
        moves = list()
        passive_left_headings = 0
        passive_right_headings = 0
        for heading, passive_moves in passive_dict.items():
            aggressive_moves = aggressive_dict[heading]
            passive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, passive_moves))
            passive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, passive_moves))
            aggressive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, aggressive_moves))
            aggressive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, aggressive_moves))
            left_right_moves = list(itertools.product(passive_left_moves,aggressive_right_moves))
            right_left_moves = list(itertools.product(passive_right_moves,aggressive_left_moves))
            moves += left_right_moves + right_left_moves
            if len(passive_left_moves) > 0:
                passive_left_headings += 1
            if len(passive_right_moves) > 0:
                passive_right_headings += 1
                
        return (moves, (passive_left_headings, passive_right_headings))
        

    def get_available_passive_moves(self, player):

        moves = [None,None,None,None]
        homeboards = self.get_homeboards(player)

        for board in homeboards:

            board_moves = {}
            player_stones = self.boards[board].stones[player]
            enemy_stones = self.boards[board].stones[(player + 1) % 2]
            all_stones = player_stones.union(enemy_stones)

            for stone in player_stones:
                
                stone_passive_moves = []

                x = stone[1]
                y = stone[0]

                left_room = min(x, 2)
                up_room = min(y, 2)
                right_room = min(3 - x, 2)
                down_room = min(3 - y, 2)

                up_left_room = min(left_room, up_room)
                up_right_room = min(right_room, up_room)
                down_right_room = min(right_room, down_room)
                down_left_room = min(left_room, down_room)

                dy = 0
                for dx in range(1, left_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y, x - dx)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(dy,-dx)))
                
                for dx in range(1, right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y, x + dx)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(dy,dx)))
                
                dx = 0
                for dy in range(1, up_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dy, x)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(-dy,dx)))

                for dy in range(1, down_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dy, x)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(dy,dx)))

                for dr in range(1, up_left_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dr, x - dr)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(-dr,-dr)))

                for dr in range(1, up_right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dr, x + dr)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(-dr,dr)))

                for dr in range(1, down_right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dr, x + dr)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(dr,dr)))

                for dr in range(1, down_left_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dr, x - dr)
                    if final_loc in all_stones:
                        break
                    else:
                        stone_passive_moves.append((final_loc,(dr,-dr)))
                board_moves[stone] = stone_passive_moves
            moves[board] = board_moves

        return moves

    def get_stone_moves(self, final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones):
            pushed = None
            if final_loc in player_stones:
                return False
            else:
                if pushed_stone_loc:
                    # There was a stone one away
                    if final_loc in enemy_stones or final_loc_plus_1 in enemy_stones or final_loc_plus_1 in player_stones:
                        # Trying to push too many stones
                        return False 
                    else:
                        if final_loc_plus_1[0] < 0 or final_loc_plus_1[1] < 0 or final_loc_plus_1[0] > 3 or final_loc_plus_1[1] > 3:
                            final_loc_plus_1 = None
                        pushed = (pushed_stone_loc, final_loc_plus_1)
                elif final_loc in enemy_stones:
                    if final_loc_plus_1 in enemy_stones or final_loc_plus_1 in player_stones:
                        return False
                    else:
                        if final_loc_plus_1[0] < 0 or final_loc_plus_1[1] < 0 or final_loc_plus_1[0] > 3 or final_loc_plus_1[1] > 3:
                            final_loc_plus_1 = None
                        pushed_stone_loc = final_loc
                        pushed = (pushed_stone_loc, final_loc_plus_1)
            return (final_loc, pushed)

    def get_board_aggressive_moves(self, player, board):
        board_moves = {}
        player_stones = self.boards[board].stones[player]
        enemy_stones = self.boards[board].stones[(player + 1) % 2]

        for stone in player_stones:
            
            stone_moves = [] # ((final coods), ((stone_pushed),(stone_pushed final coods)), (dy, dx))

            x = stone[1]
            y = stone[0]

            left_room = min(x, 2)
            up_room = min(y, 2)
            right_room = min(3 - x, 2)
            down_room = min(3 - y, 2)

            up_left_room = min(left_room, up_room)
            up_right_room = min(right_room, up_room)
            down_right_room = min(right_room, down_room)
            down_left_room = min(left_room, down_room)

            pushed_stone_loc = None

            dy = 0
            for dx in range(1, left_room+1):
                # Add move if there are no blocking stones
                final_loc = (y, x - dx)
                final_loc_plus_1 = (y, x - dx - 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (dy, -dx))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]
            
            pushed_stone_loc = None
            for dx in range(1, right_room+1):
                # Add move if there are no blocking stones
                final_loc = (y, x + dx)
                final_loc_plus_1 = (y, x + dx + 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (dy, dx))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]

            dx = 0
            pushed_stone_loc = None
            for dy in range(1, up_room+1):
                # Add move if there are no blocking stones
                final_loc = (y - dy, x)
                final_loc_plus_1 = (y - dy - 1, x)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (-dy, dx))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]

            pushed_stone_loc = None
            for dy in range(1, down_room+1):
                # Add move if there are no blocking stones
                final_loc = (y + dy, x)
                final_loc_plus_1 = (y + dy + 1, x)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (dy, dx))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]

            pushed_stone_loc = None
            for dr in range(1, up_left_room+1):
                # Add move if there are no blocking stones
                final_loc = (y - dr, x - dr)
                final_loc_plus_1 = (y - dr - 1, x - dr - 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (-dr, -dr))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]

            pushed_stone_loc = None
            for dr in range(1, up_right_room+1):
                # Add move if there are no blocking stones
                final_loc = (y - dr, x + dr)
                final_loc_plus_1 = (y - dr - 1, x + dr + 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (-dr, dr))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]

            pushed_stone_loc = None
            for dr in range(1, down_right_room+1):
                # Add move if there are no blocking stones
                final_loc = (y + dr, x + dr)
                final_loc_plus_1 = (y + dr + 1, x + dr + 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (dr, dr))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]
            
            pushed_stone_loc = None
            for dr in range(1, down_left_room+1):
                # Add move if there are no blocking stones
                final_loc = (y + dr, x - dr)
                final_loc_plus_1 = (y + dr + 1, x - dr - 1)
                move = self.get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                if move:
                    full_move = (move[0], move[1], (dr, -dr))
                    stone_moves.append(full_move)
                    if full_move[1]: 
                        # There is a pushed stone
                        pushed_stone_loc = full_move[1][0]
            board_moves[stone] = stone_moves
        return board_moves

    def get_available_aggressive_moves(self, player):

        moves = [None,None,None,None]

        for board in range(4):

            moves[board] = self.get_board_aggressive_moves(player, board)
        return moves

my_game = Game()

#my_game.get_boards_as_array()

my_game.play_game()


# my_game.try_move(0,(2,(3,0),(2,1)),(3,(3,1),(2,2)))
# my_game.try_move(1,(0,(0,0),(2,2)),(3,(0,1),(2,3)))
# my_game.try_passive_move(0,2,(3,0),(1,0))
# my_game.print_game()
# my_game.try_aggressive_move(1,2,(0,1),(1,0))
# my_game.print_game()


