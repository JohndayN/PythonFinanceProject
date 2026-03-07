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

def get_market_data(board_id: int):
    board = BOARDS.get(board_id)

    if board is None:
        raise ValueError(
            f"Invalid board_id {board_id}. Available boards: {list_boards()}"
        )

    return fetch_board(board["url"])

def list_boards():
    return {k: v["name"] for k, v in BOARDS.items()}