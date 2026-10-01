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
