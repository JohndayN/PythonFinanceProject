from .core import fetch_board

BOARDS = {
    1: {
        "name": "Auction",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-matching/1"
    },
    2: {
        "name": "Small Auction",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-matching/6"
    },
    3: {
        "name": "VNDiamond",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-hoseindex-forboard/2"
    },
    4: {
        "name": "VNFinLead",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-hoseindex-forboard/3"
    },
    5: {
        "name": "CW",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-matching/5"
    },
    6: {
        "name": "ETF",
        "url": "https://api.hsx.vn/l/api/v1/securities/load-securities-matching/3"
    }
}

def get_market_data(board="Auction"):

    # If user enters board name
    if isinstance(board, str):
        board = board.strip().lower()

        for board_id, info in BOARDS.items():
            if info["name"].lower() == board:
                return fetch_board(info["url"])

        raise ValueError(
            f"Invalid board name '{board}'. Available boards: {list_boards()}"
        )

    # If user enters board id
    if isinstance(board, int):
        info = BOARDS.get(board)

        if info is None:
            raise ValueError(
                f"Invalid board_id {board}. Available boards: {list_boards()}"
            )

        return fetch_board(info["url"])

def list_boards():
    return {k: v["name"] for k, v in BOARDS.items()}