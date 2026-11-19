from game.connect_four import ConnectFour

from agents.neural_mcts import NeuralMCTSAI
from agents.random_ai import RandomAI


game = ConnectFour()

neural_ai = NeuralMCTSAI(
    simulations=100
)

random_ai = RandomAI()

print("Mini-AlphaZero vs Random AI\n")

while not game.game_over:

    if game.current_player == 1:

        print("Neural Network MCTS Turn")

        move = neural_ai.get_move(game)

    else:

        print("Random AI Turn")

        move = random_ai.get_move(game)

    if move is None:
        break

    print("Selected Column:", move)

    game.make_move(move)

    game.display()

print("\nGame Over!")

if game.winner == 0:

    print("Result: Draw")

else:

    print("Winner:", game.winner)

    if game.winner == 1:
        print("Neural Network MCTS Won!")

    else:
        print("Random AI Won!")