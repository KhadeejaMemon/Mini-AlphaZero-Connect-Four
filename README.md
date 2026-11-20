# Mini-AlphaZero: Neural MCTS for Connect Four

A Connect Four AI that teaches itself from the rules alone, with no dataset. A CNN trained by self-play guides Monte Carlo Tree Search. Play it against Random, Minimax, Alpha-Beta, Standard MCTS or Neural MCTS.

## Results
Loss 2.15 to 1.69 over 10 self-play rounds, 100% vs Random AI from round 2. Minimax and Alpha-Beta were strongest in the tournament; Neural MCTS was about as strong as Standard MCTS.

Built with Python, PyTorch, NumPy, Pygame.
