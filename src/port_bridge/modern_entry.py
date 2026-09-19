import argparse,platform,sys
from pathlib import Path

def diagnostics(path=None):
    lines=["PortBridge diagnostics"]
    try:
        import PySide6,pyvisa
        from .core import TcpBridgeServer,VisaBridgeServer
        lines += ["status=ok","python="+platform.python_version(),"platform="+platform.platform(),"frozen="+str(bool(getattr(sys,"frozen",False))),"pyside6="+PySide6.__version__,"pyvisa="+pyvisa.__version__,"tcp_bridge="+TcpBridgeServer.__name__,"visa_bridge="+VisaBridgeServer.__name__];code=0
    except Exception as e:lines += ["status=failed","error=%s: %s"%(type(e).__name__,e)];code=1
    text="\n".join(lines)+"\n"
    if path:Path(path).write_text(text,encoding="utf-8")
    elif sys.stdout:sys.stdout.write(text)
    return code
def main():
    p=argparse.ArgumentParser();p.add_argument("--diagnostics-file");p.add_argument("--diagnostics",action="store_true");a=p.parse_args()
    if a.diagnostics or a.diagnostics_file:return diagnostics(a.diagnostics_file)
    from .gui import run_gui
    return run_gui()
if __name__=="__main__":raise SystemExit(main())
