#!/usr/bin/env python3
"""Send one FastCGI request to a role-managed Unix socket."""

import json
import socket
import struct
import sys


def record(kind: int, content: bytes) -> bytes:
    """Encode one FastCGI record for request one."""
    return struct.pack('!BBHHBB', 1, kind, 1, len(content), 0, 0) + content


def length(value: int) -> bytes:
    """Encode a FastCGI name/value length."""
    return bytes([value]) if value < 128 else struct.pack('!I', value | 0x80000000)


def receive(connection: socket.socket, size: int) -> bytes:
    """Read an entire record or reject a truncated response."""
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise RuntimeError('Truncated FastCGI response')
        data.extend(chunk)
    return bytes(data)


def request(socket_path: str, script: str) -> dict[str, str]:
    """Execute a script and return response headers, body and stderr."""
    parameters = {
        'SCRIPT_FILENAME': script,
        'SCRIPT_NAME': '/' + script.rsplit('/', 1)[-1],
        'REQUEST_METHOD': 'GET',
        'REQUEST_URI': '/probe.php',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '443',
        'HTTPS': 'on',
        'REMOTE_ADDR': '127.0.0.1',
    }
    encoded = b''.join(
        length(len(key)) + length(len(value)) + key.encode() + value.encode()
        for key, value in parameters.items()
    )
    stdout = bytearray()
    stderr = bytearray()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10)
        connection.connect(socket_path)
        connection.sendall(
            record(1, struct.pack('!HB5x', 1, 0))
            + record(4, encoded) + record(4, b'') + record(5, b'')
        )
        while True:
            header = receive(connection, 8)
            _, kind, _, size, padding, _ = struct.unpack('!BBHHBB', header)
            content = receive(connection, size)
            receive(connection, padding)
            if kind == 3:
                break
            if kind == 6:
                stdout.extend(content)
            elif kind == 7:
                stderr.extend(content)
    headers, _, body = stdout.decode().partition('\r\n\r\n')
    return {'headers': headers, 'body': body, 'stderr': stderr.decode()}


if __name__ == '__main__':
    print(json.dumps(request(sys.argv[1], sys.argv[2])))
