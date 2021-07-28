import os
from pathlib import Path
from unittest.mock import patch
import pytest
import data_scraping.tensorflow_data as tf_data


@pytest.fixture
def get_test_code():
    path = Path(os.getcwd()) / "tests" / "mock_resources" / "test_code.txt"
    with open(path, "r") as f:
        content = f.read()
        f.close()
    return content


@pytest.fixture
def get_test_model():
    return ["Conv2D", "Maxpooling2D", "Flatten", "Dense", "Dense"]


@patch("data_scraping.tensorflow_data.get_data_from_repository")
def test_get_data_from_repository(mock_get_data_from_repository):
    # function to test wether the function get_data_from_repository is working properly
    # uses the patch decorator to mock the function get_data_from_repository
    # checks if the sequential_list is filled properly
    expected = mock_get_data_from_repository("url", "driver", "startTime", "path")
    assert expected


def test_model_to_pickle(tmpdir, get_test_model):
    tf_data.model_to_pickle(get_test_model, tmpdir)
    assert len(os.listdir(tmpdir)) == 1


def test_get_layer_sequence1_helper(get_test_code):
    expected = tf_data.getLayerSequence1helper(get_test_code)
    assert len(expected) == 3


def test_get_layer_sequence2(get_test_code, tmpdir):
    tf_data.getLayerSequence2(get_test_code, tmpdir)
    assert len(os.listdir(tmpdir)) == 1
