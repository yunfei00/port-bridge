import pytest
from port_bridge.core.models import TcpBridgeConfig,VisaBridgeConfig
from port_bridge.core.protocol import ScpiLineFramer,is_scpi_query

def test_framer():
    f=ScpiLineFramer();assert f.feed(b"*ID")==[];assert f.feed(b"N?\n:RUN\nPART")==[b"*IDN?\n",b":RUN\n"];assert f.feed(b"IAL\n")==[b"PARTIAL\n"]
def test_query():
    assert is_scpi_query(b"*IDN?\n");assert not is_scpi_query(b":RUN\n");assert not is_scpi_query(b":DATA #13a?b\n")
def test_configs():
    TcpBridgeConfig(remote_host="192.0.2.10").validate()
    with pytest.raises(ValueError):TcpBridgeConfig(remote_host="x",remote_port=70000).validate()
    with pytest.raises(ValueError):VisaBridgeConfig(resource="").validate()
