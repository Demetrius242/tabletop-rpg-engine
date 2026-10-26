from __future__ import annotations

import base64
import hashlib
import struct
import threading

_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


def accept_key(sec_websocket_key: str) -> str:
    return base64.b64encode(hashlib.sha1(sec_websocket_key.encode() + _GUID).digest()).decode()


def handshake_response(sec_websocket_key: str) -> bytes:
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key(sec_websocket_key)}\r\n\r\n"
    ).encode()


def _read_exact(rfile, n: int) -> bytes | None:
    buf = bytearray()
    while len(buf) < n:
        chunk = rfile.read(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return bytes(buf)


def _read_frame(rfile):
    head = _read_exact(rfile, 2)
    if head is None:
        return None
    b0, b1 = head[0], head[1]
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    if length == 126:
        ext = _read_exact(rfile, 2)
        if ext is None:
            return None
        length = struct.unpack(">H", ext)[0]
    elif length == 127:
        ext = _read_exact(rfile, 8)
        if ext is None:
            return None
        length = struct.unpack(">Q", ext)[0]
    mask = _read_exact(rfile, 4) if masked else b"\x00\x00\x00\x00"
    if mask is None:
        return None
    data = bytearray(_read_exact(rfile, length) or b"")
    if masked:
        for i in range(length):
            data[i] ^= mask[i & 3]
    return opcode, bytes(data), fin


def recv_message(rfile):
    frame = _read_frame(rfile)
    if frame is None:
        return None, None
    opcode, data, fin = frame
    if opcode == OP_CLOSE:
        return "close", None
    if opcode == OP_PING:
        return "ping", data
    if opcode == OP_PONG:
        return "pong", data
    payload = bytearray(data)
    while not fin:
        frame = _read_frame(rfile)
        if frame is None:
            return None, None
        op2, data2, fin = frame
        if op2 == OP_CLOSE:
            return "close", None
        payload += data2
    try:
        return "text", payload.decode("utf-8")
    except UnicodeDecodeError:
        return "text", payload.decode("utf-8", "replace")


def encode_frame(payload: bytes, opcode: int = OP_TEXT) -> bytes:
    header = bytearray([0x80 | opcode])
    n = len(payload)
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header += struct.pack(">H", n)
    else:
        header.append(127)
        header += struct.pack(">Q", n)
    return bytes(header) + payload


class WebSocket:

    def __init__(self, wfile):
        self._wfile = wfile
        self._lock = threading.Lock()
        self.closed = False

    def send_text(self, text: str) -> bool:
        return self._send(text.encode("utf-8"), OP_TEXT)

    def pong(self, data: bytes) -> bool:
        return self._send(data, OP_PONG)

    def _send(self, payload: bytes, opcode: int) -> bool:
        if self.closed:
            return False
        try:
            with self._lock:
                self._wfile.write(encode_frame(payload, opcode))
                self._wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, ValueError, OSError):
            self.closed = True
            return False

    def close(self):
        if self.closed:
            return
        try:
            with self._lock:
                self._wfile.write(encode_frame(b"", OP_CLOSE))
                self._wfile.flush()
        except Exception:
            pass
        self.closed = True
