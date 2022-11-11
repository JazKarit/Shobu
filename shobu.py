import numpy as np
import random
import itertools
import copy
import threading
import time

class Board:

    def __init__(self, stones = [set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])]):
        self.stones = stones

    def make_aggressive_move(self,player,move):
        enemy = (player + 1) % 2
        self.stones[player].remove(move[0][0])
        self.stones[player].add(move[0][1])
        if move[1]:
            pushed_stone_start_coord = move[1][0]
            pushed_stone_end_coord = move[1][1]
            self.stones[enemy].remove(pushed_stone_start_coord)
            if pushed_stone_end_coord:
                self.stones[enemy].add(pushed_stone_end_coord)
    
global top_alpha


class Game:

    def __init__(self,boards = [Board([set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])]),Board([set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])]),Board([set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])]),Board([set([(3,0),(3,1),(3,2),(3,3)]),set([(0,0),(0,1),(0,2),(0,3)])])]):
        self.last_passive = None
        self.last_aggressive = None
        self.boards = boards
        self.letter_to_col = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
        self.user_player = 0
        self.ai_player = 1
        self.eval = 0
        self.best_move = None
        self.show_eval = True

    def end_game(self):
        if self.evaluation(0) > 0.99:
            print("Game Over. X's Win!")
            return True
        elif self.evaluation(1) > 0.99:
            print("Game Over. O's Win!")
            return True

        return False

    def play_ai(self, play_first = False, show_eval = True, depth=3, n_threads=1):
        self.show_eval = show_eval
        if play_first:
            self.print_game()
            self.get_user_move(self.user_player)
        while True:
            self.print_game()
            if self.end_game():
                break
            self.depth_n_ai(depth,self.ai_player, n_threads)
            self.print_game()
            if self.end_game():
                break
            self.get_user_move(self.user_player)

    def run_ai_vs_ai(self, show_eval = True, depth=3, n_threads=1):
        self.show_eval = show_eval
        while True:
            self.print_game()
            if self.end_game():
                break
            self.depth_n_ai(depth, 1, n_threads)
            self.print_game()
            if self.end_game():
                break
            self.depth_n_ai(depth, 0, n_threads)

    def play_two_player(self):
        self.show_eval = False
        while True:
            self.print_game()
            print("--------Player 1 Move--------\n")
            if self.end_game():
                break
            self.get_user_move(0)
            self.print_game()
            print("--------Player 2 Move--------\n")
            if self.end_game():
                break
            self.get_user_move(1)

    
            
    def make_move(self,player,passive_move,aggressive_move):
        enemy = (player + 1) % 2
        self.boards[passive_move[0]].stones[player].remove(passive_move[1])
        self.boards[passive_move[0]].stones[player].add(passive_move[2])
        self.boards[aggressive_move[0]].stones[player].remove(aggressive_move[1][0])
        self.boards[aggressive_move[0]].stones[player].add(aggressive_move[1][1])
        if aggressive_move[2]:
            pushed_stone_start_coord = aggressive_move[2][0]
            pushed_stone_end_coord = aggressive_move[2][1]
            self.boards[aggressive_move[0]].stones[enemy].remove(pushed_stone_start_coord)
            if pushed_stone_end_coord:
                self.boards[aggressive_move[0]].stones[enemy].add(pushed_stone_end_coord)
    
    def undo_move(self,player,passive_move,aggressive_move):
        enemy = (player + 1) % 2
        self.boards[passive_move[0]].stones[player].remove(passive_move[2])
        self.boards[passive_move[0]].stones[player].add(passive_move[1])
        self.boards[aggressive_move[0]].stones[player].remove(aggressive_move[1][1])
        self.boards[aggressive_move[0]].stones[player].add(aggressive_move[1][0])

        if aggressive_move[2]:
            pushed_stone_start_coord = aggressive_move[2][0]
            pushed_stone_end_coord = aggressive_move[2][1]
            if pushed_stone_end_coord:
                self.boards[aggressive_move[0]].stones[enemy].remove(pushed_stone_end_coord)
            self.boards[aggressive_move[0]].stones[enemy].add(pushed_stone_start_coord)

    def get_ai_random_move(self):
        passive_move, aggressive_move = random.choice(list(self.get_available_moves(self.ai_player)))
        self.last_passive = passive_move
        self.last_aggressive = (aggressive_move[0], aggressive_move[1][0], aggressive_move[2], aggressive_move[1][1])
        self.make_move(self.ai_player,passive_move,aggressive_move)

    def get_board_importances(self):
        importance_board = np.zeros(4)
        for board_num in range(4):
            num_stones_p0 = len(self.boards[board_num].stones[0])
            num_stones_p1 = len(self.boards[board_num].stones[1])
            max_stones = max(num_stones_p0, num_stones_p1)
            min_stones = min(num_stones_p0, num_stones_p1)
            if min_stones == 0:
                importance_board = np.zeros(4)
                importance_board[board_num] = 1
                return importance_board
            importance_board[board_num] = max_stones / (4 * min_stones ** 2)
        sum_importances = sum(importance_board)
        normalized_importances = importance_board / sum_importances
        return normalized_importances


    def evaluate_moves(self,moves,player,n,alpha_beta=True,alpha=-np.infty,beta=np.infty,top=True):
        global top_alpha
        enemy = (player + 1) % 2
        basic_eval = self.evaluation(player)
        best_move = None
        if basic_eval == -1 or basic_eval == 1:
            return (basic_eval, None)
        for move in moves:
            passive_move, aggressive_move = move
            self.make_move(player,passive_move,aggressive_move)

            # Look deeper        
            if n == 1:
                possible_eval = self.evaluation(player)
            else:
                followup_moves = self.get_available_moves(enemy)
                possible_eval, _ = self.evaluate_moves(followup_moves,enemy,n-1, not alpha_beta, alpha, beta, top=False)
                possible_eval *= -1
                
            # Undo the move
            self.undo_move(player,passive_move,aggressive_move)    
            
            # Alpha beta pruning
            if alpha_beta:
                if possible_eval >= beta:
                    return (beta, None)
                elif possible_eval > alpha:
                    alpha = possible_eval
                    best_move = (passive_move, aggressive_move)
            else:
                if -possible_eval <= top_alpha or -possible_eval <= alpha:
                    return (-alpha, None)
                elif -possible_eval < beta:
                    beta = -possible_eval
                    best_move = (passive_move, aggressive_move)
        if top:
            self.eval = alpha
            self.best_move = best_move
            if alpha > top_alpha:
                top_alpha = alpha
        else:
            if alpha_beta:
                return (alpha, best_move)
            else:
                return (-beta, best_move)

    def depth_n_ai(self,n,player,n_threads=1):

        start_time = time.time()

        global top_alpha
        top_alpha = -np.infty

        enemy = (player + 1) % 2
        best_move = None
        best_eval = None
        i = 0
        moves = self.get_available_moves(player)
        
        games = []
        threads = []
        for thread_num in range(n_threads):
            game = copy.deepcopy(self)
            games.append(game)
            threads.append(threading.Thread(game.evaluate_moves(moves[int(len(moves)*thread_num/n_threads):int(len(moves)*(thread_num+1)/n_threads)],player,n)))
            threads[thread_num].start()

        for thread in threads:
            thread.join()
        evals = []
        moves = []
        for thread_num in range(n_threads):
            evals.append(games[thread_num].eval)
            moves.append(games[thread_num].best_move)
        
        best_eval = np.max(evals)
        best_game = np.argmax(evals)
        best_move = moves[best_game]

        # Make the best move
        if player == self.user_player:
            self.eval = best_eval
        else:
            self.eval = -best_eval
        passive_move, aggressive_move = best_move

        self.last_passive = passive_move
        self.last_aggressive = (aggressive_move[0], aggressive_move[1][0], aggressive_move[2], aggressive_move[1][1])

        self.make_move(player,passive_move,aggressive_move)
        print("Move took %s seconds" % round(time.time() - start_time,2))

    def evaluation(self, player):
        """
        Return a basic evaluation of the game. 
        Evaluate each board based on the number of stones for each team. 
        Then combine these board evaluations based on the importance of each board.
        When a board has few stones of one player and more stones of the other player, 
        the importance goes up since the game is more likely to end with that board.
        """
        importance_board = [0, 0, 0, 0]
        eval_board = [0, 0, 0, 0]
        for board_num in range(4):
            p0_stones = len(self.boards[board_num].stones[0])
            p1_stones = len(self.boards[board_num].stones[1])
            if p0_stones == 0:
                if player == 0:
                    return -1
                else:
                    return 1
            elif p1_stones == 0:
                if player == 1:
                    return -1
                else:
                    return 1
            max_stones = max(p0_stones, p1_stones)
            min_stones = min(p0_stones, p1_stones)
            sum_stones = p0_stones + p1_stones
            importance_board[board_num] = max_stones / (min_stones ** 2)
            eval_board[board_num] = p0_stones / sum_stones
        sum_importances = sum(importance_board)
        num_stones_evaluation = np.dot(eval_board, importance_board) / sum_importances
        player_0_eval = 2 * ( num_stones_evaluation  - 0.5)
        if player == 0:
            return player_0_eval
        else:
            return -player_0_eval

    def get_user_move(self,player):
        success = False

        while not success:
            self.last_passive = None
            self.last_aggressive = None
            passive = None
            valid_passive = False
            while not passive or not valid_passive:
                passive_move_user = input("Passive Move: ")
                passive = self.parse_move(passive_move_user)
                if not passive:
                    print("Passive move must stay on the same board")
                else:
                    valid_passive = self.try_passive_move(player,passive[0],passive[1],passive[2])
            self.last_passive = passive
            print()
            self.print_game()
            
            required_aggressive_boards = [0,2]
            if passive[0] % 2 == 0:
                required_aggressive_boards = [1,3]
        
            try_aggressive_again = True
            while try_aggressive_again:
                aggressive_move_user = input("Aggressive Move: ")
                aggressive = self.parse_move(aggressive_move_user)
                if not aggressive:
                    print("Aggressive move must stay on the same board")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(player,passive[0],passive[2],passive[1])
                    continue
                if aggressive[0] not in required_aggressive_boards:
                    print("Aggressive move must happen on a board on the opposite side")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(player,passive[0],passive[2],passive[1])
                    continue
                if passive[2][0] - passive[1][0] != aggressive[2][0] - aggressive[1][0] or passive[2][1] - passive[1][1] != aggressive[2][1] - aggressive[1][1]:
                    print("Passive move and aggressive move do not match")
                    try_again = input('Press "a" to try the aggressive move again or "p" to pick a different passive move: ')
                    if try_again == 'p':
                        try_aggressive_again = False
                        # Undo passive move
                        self.try_passive_move(player,passive[0],passive[2],passive[1])
                    continue
                valid_aggressive = self.try_aggressive_move(player,aggressive[0],aggressive[1],aggressive[2])
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
                        self.try_passive_move(player,passive[0],passive[2],passive[1])


    def get_homeboards(self,player):
        if player == 0:
            return [2,3]
        else:
            return [0,1]

    def parse_move(self, move):
        """
        Parse the user's move.

        Input: Cordinate Start  Coordinate End 
               Columns are designated by letters a-h and rows are designated by numbers 1-8
               Ex. e1 g3 moves the stone at the bottom left corner of the bottom right board
                   two spaces diagonally upwards and to the right

        Output: (board, start_coord, end_coord)
                Board numbering:    + - +  + - +
                                    | 0 |  | 1 |
                                    + - +  + - +

                                    + - +  + - +
                                    | 2 |  | 3 |
                                    + - +  + - +
                Coords are of the form (y,x) with y,x in [0,3]
                y = 0 is the top row of the board, y = 3 is the bottom row of the board
                x = 0 is the left colum of the board, x = 3 is the right column of the board
                Ex. The move e1 g3 becomes (3, (3,0), (1,2))
        """
        move = move.replace(' ','')
        try:
            start_coord_x = self.letter_to_col[move[0]]
            end_coord_x = self.letter_to_col[move[2]]
            start_coord_y = 8 - int(move[1])
            end_coord_y = 8 - int(move[3])
        except:
            return None
        board_num = 0
        if start_coord_x >= 4:
            if end_coord_x >= 4:
                board_num += 1
                start_coord_x -= 4
                end_coord_x -= 4
            else:
                return None
        if start_coord_y >= 4:
            if end_coord_y >= 4:
                board_num += 2
                start_coord_y -= 4
                end_coord_y -= 4
            else:
                return None
        return (board_num, (start_coord_y,start_coord_x), (end_coord_y,end_coord_x))

    def try_move(self,player,passive,aggresive):
        """
        Attempt to make a move, but fail if move is illegal.
        """
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
        """
        Attempt to make a passive move, but fail if move is illegal.
        """
        available_passive_moves = self.get_available_passive_moves(player)[board]

        if available_passive_moves and start_coord in available_passive_moves and end_coord in list(zip(*available_passive_moves[start_coord]))[0]:
            self.boards[board].stones[player].remove(start_coord)
            self.boards[board].stones[player].add(end_coord)
            return True
        else:
            print("Invalid passive move")
            return False
    
    def try_aggressive_move(self,player,board,start_coord,end_coord):
        """
        Attempt to make an aggressive move, but fail if move is illegal.
        """
        available_aggressive_moves = self.get_available_aggressive_moves(player)[board]
        for move in available_aggressive_moves:
            if move[0][0] == start_coord and move[0][1] == end_coord:
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

        print('  + - - - - +     + - - - - +')
        row_num = 8
        for row in range(4):
            print(str(row_num) + ' | ' + get_board_row_string(0,row) + '|  ' + str(row_num) + '  | ' + get_board_row_string(1,row) + '|')
            row_num -= 1
        print('  + - - - - +     + - - - - +')
        print('    a b c d         e f g h')
        print('  + - - - - +     + - - - - +')
        for row in range(4):
            print(str(row_num) + ' | ' + get_board_row_string(2,row) + '|  ' + str(row_num) + '  | ' + get_board_row_string(3,row) + '|')
            row_num -= 1
        print('  + - - - - +     + - - - - +')
        print('    a b c d         e f g h')
        print()
        if self.show_eval:
            print("Current Evaluation: " + str(self.eval))
        print()
        
    def get_available_moves(self, player):
        """
        Return a list of all moves available to the given player.
        Each move is of the form: (passive_move, aggressive_move)
            Passive moves are of the form: (board_num, start_coord, end_coord)
            Aggressive moves are of the form: (board_num,(start_coord,end_coord),push)
                If a stone was pushed, push is of the form: (pushed_stone_start_coord, pushed_stone_end_coord) 
                    If the pushed stone was pushed off the board, pushed_stone_end_coord = None
                If no stone was pushed, push = None
        """

        # TODO: Save moves on the two unused boards for the next iteration

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
                for move in board_moves:
                    start_coord = move[0][0]
                    end_coord = move[0][1]
                    push = move[1]
                    heading = move[2]
                    if heading not in aggressive_dict.keys():
                        aggressive_dict[heading] = set()
                    aggressive_dict[heading].add((board_num,(start_coord,end_coord),push))
        moves = list()
        for heading, passive_moves in passive_dict.items():
            aggressive_moves = aggressive_dict[heading]
            passive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, passive_moves))
            passive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, passive_moves))
            aggressive_left_moves = set(filter(lambda move: move[0] == 0 or move[0] == 2, aggressive_moves))
            aggressive_right_moves = set(filter(lambda move: move[0] == 1 or move[0] == 3, aggressive_moves))
            left_right_moves = list(itertools.product(passive_left_moves,aggressive_right_moves))
            right_left_moves = list(itertools.product(passive_right_moves,aggressive_left_moves))
            moves += left_right_moves + right_left_moves
                
        return moves
        

    def get_available_passive_moves(self, player):
        """
        Return a list of moves for each board
            The moves for a board is a dictionary with key = start_coord, value = (end_coord, heading)
                heading is of the form (dy, dx) for dy, dx in [-2,2] with (dy == dx or dy == 0 or dx == 0) and not (dy == 0 and dx == 0)

        Note that this function does not check if there is a corresponding aggressive move available,
        so not all passive moves returned are neccesarily legal.
        """
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


    def get_available_aggressive_moves(self, player):

        """
        Return a list of moves for each board
            The moves for a board is a list with each element of the form:
                ((start coord, final coods), push, heading)
                If a stone was pushed, push is of the form: (pushed_stone_start_coord, pushed_stone_end_coord) 
                    If the pushed stone was pushed off the board, pushed_stone_end_coord = None
                If no stone was pushed, push = None
                heading is of the form (dy, dx) for dy, dx in [-2,2] with (dy == dx or dy == 0 or dx == 0) and not (dy == 0 and dx == 0)

        Note that this function does not check if there is a corresponding passive move available,
        so not all aggressive moves returned are neccesarily legal.
        """

        def get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones):
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


        moves = [None,None,None,None]

        for board_num in range(4):
            board_moves = [] # ((start coord, final coods), ((stone_pushed),(stone_pushed final coods)), (dy, dx))
            board = self.boards[board_num]
            player_stones = board.stones[player]
            enemy_stones = board.stones[(player + 1) % 2]

            for stone in player_stones:
                
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
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (dy, -dx))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break
                
                pushed_stone_loc = None
                for dx in range(1, right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y, x + dx)
                    final_loc_plus_1 = (y, x + dx + 1)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (dy, dx))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break

                dx = 0
                pushed_stone_loc = None
                for dy in range(1, up_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dy, x)
                    final_loc_plus_1 = (y - dy - 1, x)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (-dy, dx))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break

                pushed_stone_loc = None
                for dy in range(1, down_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dy, x)
                    final_loc_plus_1 = (y + dy + 1, x)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (dy, dx))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break

                pushed_stone_loc = None
                for dr in range(1, up_left_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dr, x - dr)
                    final_loc_plus_1 = (y - dr - 1, x - dr - 1)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (-dr, -dr))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break

                pushed_stone_loc = None
                for dr in range(1, up_right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y - dr, x + dr)
                    final_loc_plus_1 = (y - dr - 1, x + dr + 1)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (-dr, dr))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break

                pushed_stone_loc = None
                for dr in range(1, down_right_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dr, x + dr)
                    final_loc_plus_1 = (y + dr + 1, x + dr + 1)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (dr, dr))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break
                
                pushed_stone_loc = None
                for dr in range(1, down_left_room+1):
                    # Add move if there are no blocking stones
                    final_loc = (y + dr, x - dr)
                    final_loc_plus_1 = (y + dr + 1, x - dr - 1)
                    move = get_stone_moves(final_loc, final_loc_plus_1, pushed_stone_loc, player_stones, enemy_stones)
                    if move:
                        full_move = ((stone, move[0]), move[1], (dr, -dr))
                        board_moves.append(full_move)
                        if full_move[1]: 
                            # There is a pushed stone
                            pushed_stone_loc = full_move[1][0]
                    else:
                        break
            moves[board_num] = board_moves
        return moves

my_game = Game()
#my_game.play_ai(play_first=False,n_threads=4,show_eval=False)
my_game.run_ai_vs_ai(n_threads=1)
#my_game.play_two_player()