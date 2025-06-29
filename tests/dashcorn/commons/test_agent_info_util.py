import os
import psutil
import pytest

from unittest.mock import patch, MagicMock

from dashcorn.commons.agent_info_util import get_agent_id, get_mac_address, decorate_mac

@pytest.fixture(autouse=True)
def reset_agent_id():
    """Reset module-level _agent_id before each test"""
    import dashcorn.commons.agent_info_util as utils
    utils._agent_id = None
    yield
    utils._agent_id = None

def test_decorate_mac_normal():
    assert decorate_mac("aa:bb:cc:dd:ee:ff") == "-aabbccddeeff"
    assert decorate_mac("11:22:33:44:55:66", prefix_with="#") == "#112233445566"

def test_decorate_mac_none():
    assert decorate_mac(None) == ""
    assert decorate_mac(None, prefix_with="##") == ""

@patch("dashcorn.commons.agent_info_util.psutil.net_if_addrs")
def test_get_mac_address_with_interface(mock_net_if_addrs):
    mock_net_if_addrs.return_value = {
        "eth0": [MagicMock(family=psutil.AF_LINK, address="11:22:33:44:55:66")]
    }
    assert get_mac_address() == "11:22:33:44:55:66"

@patch("dashcorn.commons.agent_info_util.psutil.net_if_addrs")
def test_get_mac_address_none_found(mock_net_if_addrs):
    mock_net_if_addrs.return_value = {}
    assert get_mac_address() is None

@patch.dict(os.environ, {"DASHCORN_AGENT_ID": "custom-agent-id"})
def test_get_agent_id_from_env():
    from dashcorn.commons.agent_info_util import get_agent_id
    assert get_agent_id() == "custom-agent-id"

@patch("dashcorn.commons.agent_info_util.get_mac_address", return_value="aa:bb:cc:dd:ee:ff")
@patch("dashcorn.commons.agent_info_util.socket.gethostname", return_value="host123")
def test_get_agent_id_computed(mock_hostname, mock_mac):
    from dashcorn.commons.agent_info_util import get_agent_id
    assert get_agent_id() == "host123-aabbccddeeff"
