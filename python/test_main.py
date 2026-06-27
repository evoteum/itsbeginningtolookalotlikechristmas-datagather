import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from python.main import get_data, get_popularity


@pytest.fixture
def mock_auth_response():
    mock = MagicMock()
    mock.json.return_value = {"access_token": "test_token"}
    return mock


@pytest.fixture
def mock_track_response():
    mock = MagicMock()
    mock.json.return_value = {"popularity": 75}
    return mock


@patch("python.main.get")
@patch("python.main.post")
def test_get_data(mock_post, mock_get, mock_auth_response, mock_track_response):
    mock_post.return_value = mock_auth_response
    mock_get.return_value = mock_track_response

    response = get_data("test_client_id", "test_client_secret", "test_song_id")

    assert response is not None
    assert "popularity" in response.json()


@patch("python.main.get")
@patch("python.main.post")
def test_get_popularity(mock_post, mock_get, mock_auth_response, mock_track_response):
    mock_post.return_value = mock_auth_response
    mock_get.return_value = mock_track_response

    popularity = get_popularity("test_client_id", "test_client_secret", "test_song_id")
    assert popularity == 75


def test_data_format():
    timestamp = datetime.now().isoformat()
    assert timestamp.count("-") == 2
    assert "T" in timestamp
