import socket, threading
from .models import BridgeStats, VisaBridgeConfig
from .protocol import ScpiLineFramer, is_scpi_query

class VisaBridgeServer:
    def __init__(self, config: VisaBridgeConfig, on_event=None):
        config.validate();self.config=config;self._event=on_event;self._stop=threading.Event()
        self._listener=self._client=self._thread=None;self._lock=threading.Lock();self.stats=BridgeStats()
    def snapshot(self):return self.stats.snapshot()
    @property
    def is_running(self):return self.snapshot().running
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
        s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind((self.config.listen_host,self.config.listen_port));s.listen(4);s.settimeout(.5)
        self._listener=s;self._stop.clear();self.stats.set_running(True);self._thread=threading.Thread(target=self._accept,daemon=True);self._thread.start()
        self._emit(f"VISA bridge {self.config.listen_host}:{self.config.listen_port} -> {self.config.resource}")
    def stop(self):
        self._stop.set();self._close(self._listener);self._close(self._client);self._listener=self._client=None;self.stats.client_disconnected();self.stats.set_running(False)
    def _accept(self):
        while not self._stop.is_set():
            try:c,a=self._listener.accept()
            except socket.timeout:continue
            except OSError:break
            if not self._lock.acquire(False):self._close(c);continue
            threading.Thread(target=self._session,args=(c,a),daemon=True).start()
    def _session(self,c,a):
        import pyvisa
        rm=inst=None;framer=ScpiLineFramer();name=f"{a[0]}:{a[1]}"
        try:
            self._client=c;c.settimeout(.5);self.stats.client_connected(name)
            rm=pyvisa.ResourceManager(self.config.backend) if self.config.backend else pyvisa.ResourceManager()
            inst=rm.open_resource(self.config.resource);inst.timeout=self.config.timeout_ms;inst.read_termination=None;inst.write_termination=None
            while not self._stop.is_set():
                try:d=c.recv(self.config.recv_size)
                except socket.timeout:continue
                if not d:break
                self.stats.add_from_client(len(d))
                for msg in framer.feed(d):
                    inst.write_raw(msg)
                    if is_scpi_query(msg):
                        response=inst.read_raw();c.sendall(response);self.stats.add_to_client(len(response))
        except Exception as e:
            if not self._stop.is_set():self._emit(f"VISA bridge session error: {e}")
        finally:
            if inst:
                try:inst.close()
                except Exception:pass
            if rm:
                try:rm.close()
                except Exception:pass
            self._close(c);self._client=None;self.stats.client_disconnected();self._lock.release()
