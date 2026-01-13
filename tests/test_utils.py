import os
from pathlib import Path

import pytest

from vapor.core.utils import utils


def test_get_env_var(mocker):
    """Tests the `get_env_var` utility method"""
    # Correctly set env var for required key
    mocker.patch.dict(os.environ, {"TEST_VAR": "test"})
    test_var = utils.get_env_var("TEST_VAR")
    assert test_var == "test"
    # Ensure default isn't used
    test_var = utils.get_env_var("TEST_VAR", "foo")
    assert test_var == "test"

    # Key not found case
    os.environ.pop("TEST_VAR")
    # No default, should raise a KeyError
    with pytest.raises(KeyError):
        utils.get_env_var("TEST_VAR")
    # With default, should return the default value
    test_var = utils.get_env_var("TEST_VAR", "foo")
    assert test_var == "foo"

    # Key found but empty case
    mocker.patch.dict(os.environ, {"TEST_VAR": ""})
    # No default, should raise a ValueError
    with pytest.raises(ValueError):
        utils.get_env_var("TEST_VAR")
    # With default, should return the default value
    test_var = utils.get_env_var("TEST_VAR", "foo")
    assert test_var == "foo"


def test_set_env():
    """Tests setting environment variables from mapping"""
    # Create dummy mapping and set
    utils.set_env({"TEST_VAR": "test"})
    # Check vars
    assert os.environ["TEST_VAR"] == "test"
    # Pop to reset
    os.environ.pop("TEST_VAR")


def test_in_docker():
    """Tests in_docker method with `/.dockerenv` existence check"""
    assert utils.in_docker() == Path("/.dockerenv").exists()
