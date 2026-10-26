import heapq
import math
import time
import itertools
from dataclasses import dataclass, field
from collections import deque

# A state is a flat tuple of 9 ints, row by row. 0 is the blank.
#   (1,2,5,
#    3,4,0,      ->  (1, 2, 5, 3, 4, 0, 6, 7, 8)
#    6,7,8)

GOAL_STATE = (0, 1, 2, 3, 4, 5, 6, 7, 8)
SIZE = 3


def is_goal(state):
    return state == GOAL_STATE


def is_solvable(state):
    tiles = [t for t in state if t != 0]
    inversions = sum(
        1 for i in range(len(tiles)) for j in range(i + 1, len(tiles))
        if tiles[i] > tiles[j]
    )
    return inversions % 2 == 0


MOVES = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}


def get_neighbors(state):
    """Return a list of (action, new_state) for every legal move of the blank so we can choose from."""
    neighbors = []
    blank = state.index(0)
    row, col = divmod(blank, SIZE)

    for action, (dr, dc) in MOVES.items():
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < SIZE and 0 <= new_col < SIZE:       
            target = new_row * SIZE + new_col                  # go back to tuple indexing
            board = list(state)                                
            board[blank], board[target] = board[target], board[blank]
            neighbors.append((action, tuple(board)))
    return neighbors



@dataclass
class Node:
    state: tuple
    parent: "Node" = None      
    action: str = None         # move that produced this node from its parent
    g: int = 0                 # path cost so far 
    f: float = 0.0             # g + h 


@dataclass
class SearchResult:
    path_to_goal: list = field(default_factory=list)   
    states_on_path: list = field(default_factory=list) 
    cost_of_path: int = 0
    nodes_expanded: int = 0
    search_depth: int = 0      
    running_time: float = 0.0 
    solved: bool = False


def reconstruct_path(node):
    actions, states = [], []
    while node is not None:
        states.append(node.state)
        if node.action is not None:
            actions.append(node.action)
        node = node.parent
    actions.reverse()
    states.reverse()
    return actions, states


def manhattan(state):
    sum = 0
    for i, tile in enumerate(state):
        if tile == 0:
            continue
        row, col = divmod(i, SIZE)
        g_row, g_col = divmod(tile, SIZE)
        sum += abs(row - g_row) + abs(col - g_col)
    return sum


def euclidean(state):
    sum = 0.0
    for i, tile in enumerate(state):
        if tile == 0:
            continue
        row, col = divmod(i, SIZE)
        g_row, g_col = divmod(tile, SIZE)
        sum_val += math.sqrt((row - g_row)**2 + (col - g_col)**2)
    return sum_val


def a_star(initial_state, heuristic):
    """A* search. `heuristic` is a function: state -> number (manhattan/euclidean)."""
    start_time = time.perf_counter()
    result = SearchResult()

    counter = itertools.count()                      
    start = Node(initial_state, None, None, 0, heuristic(initial_state))
    frontier = [(start.f, next(counter), start)]      
    best_g = {initial_state: 0}                      
    explored = set()    
    
    while frontier:
        _, _, node = heapq.heappop(frontier)      

        if node.state in explored:                   
            continue
        explored.add(node.state)

        result.nodes_expanded += 1
        result.search_depth = max(result.search_depth, node.g)

        if is_goal(node.state):
            result.path_to_goal, result.states_on_path = reconstruct_path(node)
            result.cost_of_path = node.g
            result.solved = True
            break

        for action, next_state in get_neighbors(node.state):
            new_g = node.g + 1                        
            if next_state not in explored and new_g < best_g.get(next_state, float("inf")):
                best_g[next_state] = new_g
                child = Node(next_state, node, action, new_g, new_g + heuristic(next_state))
                heapq.heappush(frontier, (child.f, next(counter), child))

    result.running_time = time.perf_counter() - start_time
    return result


def print_board(state):
    border = "+" + "---+" * SIZE
    print(border)
    for r in range(SIZE):
        row = state[r * SIZE:(r + 1) * SIZE]               
        cells = []
        for t in row:
            if t != 0:
                cells.append(str(t))
            else:
                cells.append(" ")   
        print("| " + " | ".join(cells) + " |")
        print(border)

# the old print function if absolute every step needs to be shown

# def print_solution(result, initial_state):
#     if not result.solved:
#         print("No solution found.")
#         return

#     print("Path:", " -> ".join(result.path_to_goal))
#     print(f"Cost: {result.cost_of_path} moves\n")

#     for step, state in enumerate(result.states_on_path):
#         print("Initial state" if step == 0 else f"Step {step}")
#         print_board(state)

def print_solution(result, initial_state):
    if not result.solved:
        print("No solution found.")
        return

    # Truncates the raw path string if it's so long
    path_str = " -> ".join(result.path_to_goal)
    if len(path_str) > 150:
        path_str = path_str[:147] + "..."

    print(f"Path: {path_str}")
    print(f"Cost: {result.cost_of_path} moves\n")

    total_steps = len(result.states_on_path)
    
    # If the path is a reasonable length like A*, BFS, IDS functions, print all steps
    if total_steps <= 50:
        for step, state in enumerate(result.states_on_path):
            print("Initial state" if step == 0 else f"Step {step}")
            print_board(state)  
    else:
        # If the path is massive (DFS), print the first 5 and last 5 steps
        for step in range(5):
            print("Initial state" if step == 0 else f"Step {step}")
            print_board(result.states_on_path[step])
            
        print(f"\n... [ {total_steps - 10} steps hidden to prevent terminal freeze ] ...\n")
        
        for step in range(total_steps - 5, total_steps):
            print(f"Step {step}")
            print_board(result.states_on_path[step])

def generate_fancy_board(state):
    """Generates a clean Unicode box-drawing visualization for the board."""
    top = "┌───┬───┬───┐\n"

    mid = "├───┼───┼───┤\n"

    bot = "└───┴───┴───┘\n"
    
    lines = [top]
    for r in range(SIZE):
        row = state[r * SIZE : (r + 1) * SIZE]
        cells = [str(t) if t != 0 else " " for t in row]
        lines.append("│ " + " │ ".join(cells) + " │\n")
        if r < SIZE - 1:
            lines.append(mid)
    lines.append(bot)
    return "".join(lines)

def export_results_to_file(results, initial_state, filename="8_puzzle_results.txt"):
    """Writes the history to a text file with a safety cap for massive DFS paths."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write(" " * 15 + "8-PUZZLE SEARCH RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("Initial State:\n")
        f.write(generate_fancy_board(initial_state) + "\n")
        
        for name, result in results:
            f.write("-" * 60 + "\n")
            f.write(f"Algorithm: {name}\n")
            f.write("-" * 60 + "\n")
            
            if not result.solved:
                f.write("No solution found.\n\n")
                continue
                
            f.write(f"Cost (Moves)   : {result.cost_of_path}\n")
            f.write(f"Nodes Expanded : {result.nodes_expanded}\n")
            f.write(f"Search Depth   : {result.search_depth}\n")
            f.write(f"Running Time   : {result.running_time:.6f} seconds\n")
            
            # Cap the path string length
            path_str = " -> ".join(result.path_to_goal)
            if len(path_str) > 150:
                f.write(f"Complete Path  : {path_str[:147]}...\n\n")
            else:
                f.write(f"Complete Path  : {path_str}\n\n")
            
            f.write("Step-by-Step Visualization:\n\n")
            total_steps = len(result.states_on_path)
            
            # Print everything if it's a reasonable length
            if total_steps <= 200:
                for step, state in enumerate(result.states_on_path):
                    move = "" if step == 0 else f" (Moved {result.path_to_goal[step-1]})"
                    f.write("Initial state\n" if step == 0 else f"Step {step}{move}\n")
                    f.write(generate_fancy_board(state) + "\n")
            
            # Otherwise, print the first 50 and last 50
            else:
                for step in range(50):
                    move = "" if step == 0 else f" (Moved {result.path_to_goal[step-1]})"
                    f.write("Initial state\n" if step == 0 else f"Step {step}{move}\n")
                    f.write(generate_fancy_board(result.states_on_path[step]) + "\n")
                    
                f.write(f"\n... [ {total_steps - 100} steps hidden to prevent text viewer crashing lol ] ...\n\n")
                
                for step in range(total_steps - 50, total_steps):
                    move = f" (Moved {result.path_to_goal[step-1]})"
                    f.write(f"Step {step}{move}\n")
                    f.write(generate_fancy_board(result.states_on_path[step]) + "\n")
            f.write("\n")

def print_report_header():
    print(f"{'Algorithm':<14}{'Cost':>6}{'Expanded':>10}{'Depth':>7}{'Time (s)':>11}  Path")
    print("-" * 80)


def print_report_row(name, result):
    path = ",".join(result.path_to_goal)
    if len(path) > 40:                                  
        path = path[:37] + "..."
    print(f"{name:<14}{result.cost_of_path:>6}{result.nodes_expanded:>10}"
          f"{result.search_depth:>7}{result.running_time:>11.6f}  {path}")


def read_initial_state():
    while True:
        text = input("Enter the initial state (9 numbers, 0 = blank): ")
        text = text.replace(",", " ")            
        try:
            state = tuple(int(x) for x in text.split())
        except ValueError:
            print("Please enter numbers only.\n")
            continue

        if sorted(state) != list(range(SIZE * SIZE)):
            print("The board must contain each number from 0 to 8 exactly once.\n")
            continue

        return state
    



def bfs(initial_state):
    
    start_time = time.perf_counter()
    result = SearchResult()

    start = Node(initial_state, None, None, 0, 0.0)
    frontier = deque([start])
    
    # Using a reached set to not deal with dublicates
    reached = {initial_state}

    while frontier:
        node = frontier.popleft()

        result.nodes_expanded += 1
        result.search_depth = max(result.search_depth, node.g)

        if is_goal(node.state):
            result.path_to_goal, result.states_on_path = reconstruct_path(node)
            result.cost_of_path = node.g
            result.solved = True
            break

        for action, next_state in get_neighbors(node.state):
            if next_state not in reached:
                reached.add(next_state)
                child = Node(next_state, node, action, node.g + 1, 0.0)
                frontier.append(child)

    result.running_time = time.perf_counter() - start_time
    return result


def dfs(initial_state):
    
    start_time = time.perf_counter()
    result = SearchResult()

    start = Node(initial_state, None, None, 0, 0.0)
    frontier = [start]
    explored = set()

    while frontier:
        node = frontier.pop()

        if node.state in explored:
            continue
        explored.add(node.state)

        result.nodes_expanded += 1
        result.search_depth = max(result.search_depth, node.g)

        if is_goal(node.state):
            result.path_to_goal, result.states_on_path = reconstruct_path(node)
            result.cost_of_path = node.g
            result.solved = True
            break

        # Reverse the moves so the stack pops them in the normal order
        for action, next_state in reversed(get_neighbors(node.state)):
            if next_state not in explored:
                child = Node(next_state, node, action, node.g + 1, 0.0)
                frontier.append(child)

    result.running_time = time.perf_counter() - start_time
    return result


def ids(initial_state):

    start_time = time.perf_counter()
    result = SearchResult()
    depth_limit = 0

    while True:
        start = Node(initial_state, None, None, 0, 0.0)
        frontier = [start]
        # Tracks the minimum depth at which a state was visited during this iteration
        visited = {}

        while frontier:
            node = frontier.pop()

            # Cycle checking to skip if we've seen this state at an equal or shallower depth this iteration
            if node.state in visited and visited[node.state] <= node.g:
                continue
            visited[node.state] = node.g

            result.nodes_expanded += 1
            result.search_depth = max(result.search_depth, node.g)

            if is_goal(node.state):
                result.path_to_goal, result.states_on_path = reconstruct_path(node)
                result.cost_of_path = node.g
                result.solved = True
                result.running_time = time.perf_counter() - start_time
                return result

            # Only expand if we are below the current depth limit
            if node.g < depth_limit:
                for action, next_state in reversed(get_neighbors(node.state)):
                    child = Node(next_state, node, action, node.g + 1, 0.0)
                    frontier.append(child)

        depth_limit += 1


if __name__ == "__main__":
    initial = read_initial_state()

    if not is_solvable(initial):
        print("Unsolvable board")
    else:
        algorithms = [
            ("A* Manhattan", lambda s: a_star(s, manhattan)),
            ("A* Euclidean", lambda s: a_star(s, euclidean)),
            ("BFS", bfs),
            ("DFS", dfs),
            ("IDS", ids),
        ]

        results = []
        for name, algo in algorithms:
            try:
                result = algo(initial)
            except NotImplementedError:
                print(f"{name}: skip\n")
                continue
            print("-" * 40)
            print(f"{name}")
            print("-" * 40)
            print_solution(result, initial)
            print()
            results.append((name, result))

        print("COMPARISON")
        print_report_header()
        for name, result in results:
            print_report_row(name, result)

        # ask user if he wnats to export full results
        print("\n" + "="*80)
        export = input("Do you want to export the full, untruncated results to a text file? (y/n): ").strip().lower()
        if export == 'y':
            export_results_to_file(results, initial)
            print("\nSuccessfully exported complete traceable results to '8_puzzle_results.txt")
