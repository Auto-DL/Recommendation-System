from unittest.mock import patch
import data_scraping.tensorflow_data as tf_data


@patch("data_scraping.tensorflow_data.get_data_from_repository")
def test_get_data_from_repository(mock_get_data_from_repository):
    # function to test wether the function get_data_from_repository is working properly
    # uses the patch decorator to mock the function get_data_from_repository
    # checks if the sequential_list is filled properly
    expected = mock_get_data_from_repository("url", "driver", "startTime", "path")
    assert expected
