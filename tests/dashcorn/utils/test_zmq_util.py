import os
import errno
import pytest
import stat
from unittest.mock import patch, MagicMock

from dashcorn.utils.zmq_util import renew_zmq_ipc_socket

@pytest.mark.parametrize("protocol", [None, "tcp"])
@patch("os.path.exists", return_value=True)
@patch("os.remove")
def test_no_remove_for_non_ipc(mock_remove, mock_exists, protocol):
    ipc_path = "/tmp/socket"
    result = renew_zmq_ipc_socket(ipc_path, protocol=protocol)
    mock_remove.assert_not_called()
    assert result == ipc_path

@patch("os.path.exists", return_value=True)
@patch("os.stat")
@patch("os.remove")
def test_remove_socket_file(mock_remove, mock_stat, mock_exists):
    ipc_path = "/tmp/test_socket"
    mock_stat.return_value.st_mode = stat.S_IFSOCK
    result = renew_zmq_ipc_socket(ipc_path, protocol="ipc", strict=True)
    mock_remove.assert_called_once_with(ipc_path)
    assert result == ipc_path

@patch("os.path.exists", return_value=True)
@patch("os.stat")
@patch("os.remove")
def test_refuse_remove_non_socket(mock_remove, mock_stat, mock_exists):
    ipc_path = "/tmp/test_file"
    mock_stat.return_value.st_mode = stat.S_IFREG  # regular file
    with pytest.raises(RuntimeError, match="Refusing to remove non-socket file"):
        renew_zmq_ipc_socket(ipc_path, protocol="ipc", strict=True)
    mock_remove.assert_not_called()

@patch("os.path.exists", return_value=True)
@patch("os.remove", side_effect=OSError(errno.EBUSY, "Device or resource busy"))
@patch("os.stat", return_value=MagicMock(st_mode=stat.S_IFSOCK))
def test_ebusy_removal_error(mock_stat, mock_remove, mock_exists):
    ipc_path = "/tmp/test_busy"
    with pytest.raises(RuntimeError, match="Cannot remove busy socket file"):
        renew_zmq_ipc_socket(ipc_path, protocol="ipc", strict=True)

@patch("os.path.exists", return_value=True)
@patch("os.remove", side_effect=OSError(errno.EPERM, "Permission denied"))
@patch("os.stat", return_value=MagicMock(st_mode=stat.S_IFSOCK))
def test_general_removal_error(mock_stat, mock_remove, mock_exists):
    ipc_path = "/tmp/test_perm"
    with pytest.raises(RuntimeError, match="Failed to remove existing file"):
        renew_zmq_ipc_socket(ipc_path, protocol="ipc", strict=True)

@patch("os.path.exists", return_value=True)
@patch("os.remove")
def test_strict_false_allows_regular_file(mock_remove, mock_exists):
    ipc_path = "/tmp/test_regular"
    result = renew_zmq_ipc_socket(ipc_path, protocol="ipc", strict=False)
    mock_remove.assert_called_once_with(ipc_path)
    assert result == ipc_path
