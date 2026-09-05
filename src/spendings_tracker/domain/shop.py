"""Shop match after trim and case; remaining spelling must be exact."""


def shop_key(display: str) -> str:
    return display.strip().lower()


def shops_match(left: str, right: str) -> bool:
    return shop_key(left) == shop_key(right)
