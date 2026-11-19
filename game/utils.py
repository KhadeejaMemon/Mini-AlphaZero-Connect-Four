def drop_piece(board, col, player):
    """Piece girata hai aur row return karta hai."""
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return row
    return -1


def wins_at(board, row, col, player):
    """Sirf last move ke around check karta hai (poore board se bahut tez)."""
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1
        for sign in (1, -1):
            r = row + dr * sign
            c = col + dc * sign
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr * sign
                c += dc * sign
        if count >= 4:
            return True
    return False