import os
from pathlib import Path
from unittest.mock import patch
import pytest
import data_scraping.tensorflow_data as tf_data

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


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


@pytest.fixture
def get_test_rawLayerSequence(get_test_code):
    return tf_data.getLayerSequence1helper(get_test_code)


@pytest.fixture
def get_driver():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(
        ChromeDriverManager(path="./").install(), options=options
    )  # downloads the latest version of the chrome drivers
    return driver


@pytest.fixture
def get_test_repository_url():
    return "https://github.com/bamblebam/image-classification-rps"


def test_get_data_from_repository(get_test_repository_url, get_driver, tmpdir):
    startTimeForUrl = time.time()
    tf_data.get_data_from_repository(
        get_test_repository_url, get_driver, startTimeForUrl, tmpdir
    )
    assert len(os.listdir(tmpdir)) == 27


def test_model_to_pickle(tmpdir, get_test_model):
    tf_data.model_to_pickle(get_test_model, tmpdir)
    assert len(os.listdir(tmpdir)) == 1


def test_get_layer_sequence1_helper(get_test_code):
    expected = tf_data.getLayerSequence1helper(get_test_code)
    assert len(expected) == 4


def test_get_cleaned_layers(get_test_rawLayerSequence, tmpdir):
    tf_data.getCleanedLayers(get_test_rawLayerSequence, tmpdir)
    assert len(os.listdir(tmpdir)) == 2


def test_get_layer_sequence1(get_test_code, tmpdir):
    tf_data.getLayerSequence1(get_test_code, tmpdir)
    assert len(os.listdir(tmpdir)) == 2


def test_get_layer_sequence2(get_test_code, tmpdir):
    tf_data.getLayerSequence2(get_test_code, tmpdir)
    assert len(os.listdir(tmpdir)) == 1


def test_get_model_arrays(get_test_code, tmpdir):
    tf_data.get_model_arrays(get_test_code, tmpdir)
    assert len(os.listdir(tmpdir)) == 3


@patch("builtins.print")
@patch("data_scraping.tensorflow_data.get_data_from_repository")
def test_main(mock_get_data_from_repository, mock_print, tmpdir):
    startDate = "2020-04-05"
    endDate = "2020-04-06"
    tf_data.main(startDate, endDate, tmpdir)
    mock_print.assert_called_with("Finished")


def test_getDates():
    dates = tf_data.getDates("2020-01", "2020-02")
    assert len(dates) == 8
