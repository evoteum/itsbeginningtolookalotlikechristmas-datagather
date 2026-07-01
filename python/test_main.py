import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from python.main import get_data, get_popularity


@pytest.fixture
def mock_track_response():
    mock = MagicMock()
    mock.json.return_value = {
        "data": [
            {
                "title": "It's Beginning to Look a Lot Like Christmas",
                "artist": {"name": "Perry Como"},
                "rank": 750000,
            }
        ]
    }
    return mock


@patch("python.main.get")
def test_get_data(mock_get, mock_track_response):
    mock_get.return_value = mock_track_response

    response = get_data("Perry Como", "It's Beginning to Look a Lot Like Christmas")

    assert response is not None
    assert "data" in response.json()


@patch("python.main.get")
def test_get_popularity(mock_get, mock_track_response):
    mock_get.return_value = mock_track_response

    popularity = get_popularity("Perry Como", "It's Beginning to Look a Lot Like Christmas")
    assert popularity == 75


def test_data_format():
    timestamp = datetime.now().isoformat()
    assert timestamp.count("-") == 2
    assert "T" in timestamp
