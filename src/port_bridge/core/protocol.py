class ScpiLineFramer:
    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes):
        if data:
            self._buffer.extend(data)
        messages = []
        while True:
            try:
                index = self._buffer.index(0x0A)
            except ValueError:
                break
            end = index + 1
            messages.append(bytes(self._buffer[:end]))
            del self._buffer[:end]
        return messages

    @property
    def pending_bytes(self):
        return len(self._buffer)


def is_scpi_query(message: bytes) -> bool:
    command_part = message.split(b"#", 1)[0].rstrip(b"\r\n \t")
    return b"?" in command_part
