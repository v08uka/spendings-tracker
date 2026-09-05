from spendings_tracker.__main__ import main


def test_app_boots() -> None:
    assert main([]) == 0
