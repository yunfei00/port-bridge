from dataclasses import dataclass
from threading import Lock
from time import monotonic

@dataclass
class TcpBridgeConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 15025
    remote_host: str = "127.0.0.1"
    remote_port: int = 5025
    connect_timeout_s: float = 5.0
    recv_size: int = 65536
    def validate(self):
        _common(self.listen_host, self.listen_port, self.recv_size)
        if not self.remote_host.strip(): raise ValueError("remote_host must not be empty")
        _port("remote_port", self.remote_port)
        if self.connect_timeout_s <= 0: raise ValueError("connect_timeout_s must be greater than zero")

@dataclass
class VisaBridgeConfig:
    resource: str
    listen_host: str = "0.0.0.0"
    listen_port: int = 15026
    timeout_ms: int = 5000
    recv_size: int = 65536
    backend: str = None
    def validate(self):
        _common(self.listen_host, self.listen_port, self.recv_size)
        if not self.resource.strip(): raise ValueError("VISA resource must not be empty")
        if self.timeout_ms <= 0: raise ValueError("timeout_ms must be greater than zero")

def _common(host, port, recv_size):
    if not host.strip(): raise ValueError("listen_host must not be empty")
    _port("listen_port", port)
    if recv_size < 1024: raise ValueError("recv_size must be at least 1024 bytes")

def _port(name, value):
    if not 1 <= int(value) <= 65535: raise ValueError(f"{name} must be between 1 and 65535")

@dataclass(frozen=True)
class BridgeStatsSnapshot:
    bytes_from_client: int
    bytes_to_client: int
    client_address: str
    connected_seconds: float
    running: bool

class BridgeStats:
    def __init__(self):
        self._lock=Lock(); self._from=0; self._to=0; self._client=None; self._at=None; self._running=False
    def set_running(self,v):
        with self._lock:self._running=v
    def client_connected(self,a):
        with self._lock:self._client=a;self._at=monotonic()
    def client_disconnected(self):
        with self._lock:self._client=None;self._at=None
    def add_from_client(self,n):
        with self._lock:self._from+=max(0,n)
    def add_to_client(self,n):
        with self._lock:self._to+=max(0,n)
    def snapshot(self):
        with self._lock:
            sec=None if self._at is None else max(0.0,monotonic()-self._at)
            return BridgeStatsSnapshot(self._from,self._to,self._client,sec,self._running)
