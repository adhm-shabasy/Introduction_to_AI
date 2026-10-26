import random
from flask import Flask, jsonify, render_template, request
import puzzle

app = Flask(__name__)

ALGORITHMS = {
    "astar_manhattan": ("A* Manhattan", lambda s: puzzle.a_star(s, puzzle.manhattan)),
    "astar_euclidean": ("A* Euclidean", lambda s: puzzle.a_star(s, puzzle.euclidean)),
    "bfs": ("BFS", puzzle.bfs),
    "dfs": ("DFS", puzzle.dfs),
    "ids": ("IDS", puzzle.ids),
}


def check_state(state):
    if not isinstance(state, list) or len(state) != 9:
        return "Enter exactly 9 numbers."
    if sorted(state) != list(range(9)):
        return "The board must contain each number from 0 to 8 exactly once."
    if not puzzle.is_solvable(tuple(state)):
        return "This board is unsolvable."
    return None


@app.route("/")
def home():
    algos = [{"key": k, "name": v[0]} for k, v in ALGORITHMS.items()]
    return render_template("index.html", algos=algos)


@app.route("/check", methods=["POST"])
def check():
    error = check_state(request.json.get("state"))
    return jsonify(ok=error is None, error=error)


@app.route("/random")
def random_board():
    while True:
        board = list(range(9))
        random.shuffle(board)
        if puzzle.is_solvable(tuple(board)):
            return jsonify(state=board)


@app.route("/solve/<key>", methods=["POST"])
def solve(key):
    if key not in ALGORITHMS:
        return jsonify(error="Unknown algorithm"), 404

    state = request.json.get("state")
    error = check_state(state)
    if error:
        return jsonify(error=error), 400

    name, algo = ALGORITHMS[key]
    result = algo(tuple(state))

    return jsonify(
        key=key,
        name=name,
        solved=result.solved,
        cost=result.cost_of_path,
        nodes_expanded=result.nodes_expanded,
        depth=result.search_depth,
        time=result.running_time,
        moves=result.path_to_goal,
        states=result.states_on_path,
    )


if __name__ == "__main__":
    app.run(debug=True)