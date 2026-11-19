import random
import time

from game.connect_four import ConnectFour


def random_opening(plies=2):
    game = ConnectFour()
    opening = []
    for _ in range(plies):
        col = random.choice(game.get_valid_moves())
        game.make_move(col)
        opening.append(col)
    return opening


def play_game(first_agent, second_agent, opening=()):
    game = ConnectFour()

    for col in opening:
        game.make_move(col)

    agents = {1: first_agent, -1: second_agent}
    times = {1: [], -1: []}

    while not game.game_over:
        player = game.current_player

        start = time.perf_counter()
        move = agents[player].get_move(game)
        times[player].append(time.perf_counter() - start)

        if move not in game.get_valid_moves():
            raise ValueError(f"Invalid move {move} by player {player}")

        game.make_move(move)

    return game.winner, times


def play_match(agent_a, agent_b, num_pairs=10, opening_plies=2):
    """Har pair: same random opening, agent_a pehle phir agent_b pehle.
    Total games = 2 * num_pairs."""

    r = {
        "a_wins": 0, "b_wins": 0, "draws": 0, "games": 0,
        "a_time": 0.0, "a_moves": 0, "b_time": 0.0, "b_moves": 0,
    }

    for _ in range(num_pairs):

        opening = random_opening(opening_plies)

        for a_first in (True, False):

            if a_first:
                first, second = agent_a, agent_b
                a_player, b_player = 1, -1
            else:
                first, second = agent_b, agent_a
                a_player, b_player = -1, 1

            winner, times = play_game(first, second, opening)

            if winner == 0:
                r["draws"] += 1
            elif winner == a_player:
                r["a_wins"] += 1
            else:
                r["b_wins"] += 1

            r["a_time"] += sum(times[a_player])
            r["b_time"] += sum(times[b_player])
            r["a_moves"] += len(times[a_player])
            r["b_moves"] += len(times[b_player])
            r["games"] += 1

    return r