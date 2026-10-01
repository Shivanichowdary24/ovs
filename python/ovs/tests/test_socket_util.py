import errno
from unittest import mock

from ovs import socket_util


def test_write_fully_partial_write():
    writes = []

    def partial_write(fd, buf):
        writes.append(buf)
        if len(writes) == 1:
            return 3
        return len(buf)

    with mock.patch("ovs.socket_util.os.write", side_effect=partial_write):
        error, bytes_written = socket_util.write_fully(123, b"ABCDEFGH")

    assert error == 0
    assert bytes_written == 8
    assert writes == [b"ABCDEFGH", b"DEFGH"]


def test_make_unix_socket_closes_socket_on_unlink_error():
    fake_sock = mock.MagicMock()
    unlink_error = OSError(errno.EACCES, "Permission denied")

    with mock.patch("ovs.socket_util.socket.socket",
                    return_value=fake_sock), \
         mock.patch("ovs.socket_util.os.unlink",
                    side_effect=unlink_error):
        error, sock = socket_util.make_unix_socket(
            socket_util.socket.SOCK_STREAM,
            False,
            "/tmp/ovs-test.sock",
            None,
        )

    assert error == errno.EACCES
    assert sock is None
    fake_sock.close.assert_called_once()

def test_make_unix_socket_closes_connect_dirfd_on_bind_open_error():
    fake_sock = mock.MagicMock()
    fake_sock.bind.side_effect = socket_util.socket.error(
        "AF_UNIX path too long"
    )

    bind_path = "/tmp/ovs-bind/socket"
    connect_path = "/tmp/ovs-connect/socket"

    with mock.patch("ovs.socket_util.socket.socket",
                    return_value=fake_sock), \
         mock.patch("ovs.socket_util.os.unlink"), \
         mock.patch("ovs.socket_util.os.path.exists",
                    return_value=False), \
         mock.patch("ovs.socket_util.os.uname",
                    return_value=("Linux", "", "", "", "")), \
         mock.patch("ovs.socket_util.os.open",
                    side_effect=[
                        42,
                        OSError(errno.EACCES, "Permission denied"),
                    ]), \
         mock.patch("ovs.socket_util.os.close") as mock_close:
        error, sock = socket_util.make_unix_socket(
            socket_util.socket.SOCK_STREAM,
            False,
            bind_path,
            connect_path,
        )

    assert error == errno.EACCES
    assert sock is None
    mock_close.assert_called_once_with(42)