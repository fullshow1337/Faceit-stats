import pytest

from api_clients.fast_api_client_httpx import FastFaceitClientHttpx


def test_determine_result_by_winner_team_id_win():
    client = FastFaceitClientHttpx(api_key="test")
    match_details = {
        "results": {"winner": "team_1"},
        "teams": [
            {"team_id": "team_1", "players": [{"player_id": "p1"}]},
            {"team_id": "team_2", "players": [{"player_id": "p2"}]},
        ],
    }
    assert client._determine_match_result(match_details, "p1") == "Win"


def test_determine_result_by_winner_team_id_lose():
    client = FastFaceitClientHttpx(api_key="test")
    match_details = {
        "results": {"winner": "team_2"},
        "teams": [
            {"team_id": "team_1", "players": [{"player_id": "p1"}]},
            {"team_id": "team_2", "players": [{"player_id": "p2"}]},
        ],
    }
    assert client._determine_match_result(match_details, "p1") == "Lose"


def test_determine_result_by_score_and_faction_draw():
    client = FastFaceitClientHttpx(api_key="test")
    match_details = {
        "results": {"score": "12/12"},
        "factions": {
            "faction1": {"players": [{"player_id": "p1"}]},
            "faction2": {"players": [{"player_id": "p2"}]},
        },
    }
    assert client._determine_match_result(match_details, "p1") == "Draw"


