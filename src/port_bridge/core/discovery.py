"""Endpoint discovery and connection-test helpers."""

import socket


def list_visa_resources(backend=None):
    import pyvisa
    manager = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
    try:
        resources = list(manager.list_resources())
    finally:
        manager.close()
    return sorted(resources, key=lambda item: (not item.upper().startswith("USB"), item))


def test_tcp_endpoint(host, port, timeout_s=5.0, command=b"*IDN?\n"):
    with socket.create_connection((host, port), timeout=timeout_s) as sock:
        sock.settimeout(timeout_s)
        sock.sendall(command)
        chunks, total = [], 0
        while total < 65536:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
            total += len(data)
            if b"\n" in data:
                break
        return b"".join(chunks).decode("utf-8", errors="replace").strip()


def test_visa_endpoint(resource, timeout_ms=5000, backend=None):
    import pyvisa
    manager = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
    instrument = manager.open_resource(resource)
    try:
        instrument.timeout = timeout_ms
        instrument.read_termination = "\n"
        instrument.write_termination = "\n"
        return instrument.query("*IDN?").strip()
    finally:
        instrument.close()
        manager.close()
