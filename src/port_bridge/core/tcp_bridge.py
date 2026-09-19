import socket, threading
from .models import BridgeStats, TcpBridgeConfig

class TcpBridgeServer:
    def __init__(self, config: TcpBridgeConfig, on_event=None):
        config.validate(); self.config=config; self._event=on_event; self._stop=threading.Event()
        self._listener=self._client=self._upstream=self._thread=None; self._lock=threading.Lock(); self.stats=BridgeStats()
    def snapshot(self): return self.stats.snapshot()
    @property
    def is_running(self): return self.snapshot().running
    def _emit(self,m):
        if self._event:
            try:self._event(m)
            except Exception:pass
    @staticmethod
    def _close(s):
        if not s:return
        try:s.shutdown(socket.SHUT_RDWR)
        except OSError:pass
        try:s.close()
        except OSError:pass
    def start(self):
        if self.is_running:return
        s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.config.listen_host,self.config.listen_port));s.listen(4);s.settimeout(.5)
        self._listener=s;self._stop.clear();self.stats.set_running(True)
        self._thread=threading.Thread(target=self._accept,daemon=True);self._thread.start()
        self._emit(f"TCP bridge {self.config.listen_host}:{self.config.listen_port} -> {self.config.remote_host}:{self.config.remote_port}")
    def stop(self):
        self._stop.set()
        for s in (self._listener,self._client,self._upstream):self._close(s)
        self._listener=self._client=self._upstream=None;self.stats.client_disconnected();self.stats.set_running(False)
        self._emit("TCP bridge stopped")
    def _accept(self):
        while not self._stop.is_set():
            try:c,a=self._listener.accept()
            except socket.timeout:continue
            except OSError:break
            if not self._lock.acquire(False):self._emit(f"Rejected extra client {a[0]}:{a[1]}");self._close(c);continue
            threading.Thread(target=self._session,args=(c,a),daemon=True).start()
    def _session(self,c,a):
        u=None; name=f"{a[0]}:{a[1]}"
        try:
            self._client=c;self.stats.client_connected(name);self._emit(f"Client connected: {name}")
            u=socket.create_connection((self.config.remote_host,self.config.remote_port),timeout=self.config.connect_timeout_s)
            u.settimeout(None);c.settimeout(None);self._upstream=u
            done=threading.Event()
            threading.Thread(target=self._pump,args=(c,u,True,done),daemon=True).start()
            threading.Thread(target=self._pump,args=(u,c,False,done),daemon=True).start();done.wait()
        except Exception as e:self._emit(f"TCP bridge session error: {e}")
        finally:
            self._close(c);self._close(u);self._client=self._upstream=None;self.stats.client_disconnected();self._emit(f"Client disconnected: {name}");self._lock.release()
    def _pump(self,source,target,from_client,done):
        try:
            while not self._stop.is_set() and not done.is_set():
                d=source.recv(self.config.recv_size)
                if not d:break
                target.sendall(d)
                (self.stats.add_from_client if from_client else self.stats.add_to_client)(len(d))
        except OSError as e:
            if not self._stop.is_set():self._emit(f"TCP stream closed: {e}")
        finally:done.set();self._close(source);self._close(target)
