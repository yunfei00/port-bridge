#!/usr/bin/env python3
"""Legacy PortBridge UI for old Windows/FSW systems (Python 3.8 + Tkinter)."""
import argparse,json,os,platform,queue,sys,threading
from datetime import datetime
from pathlib import Path
from .core import TcpBridgeConfig,TcpBridgeServer,VisaBridgeConfig,VisaBridgeServer,list_visa_resources,test_tcp_endpoint,test_visa_endpoint

def _settings_path():
    base=os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    folder=Path(base)/"PortBridge"/"Legacy";folder.mkdir(parents=True,exist_ok=True);return folder/"settings.json"
def _load():
    try:return json.loads(_settings_path().read_text(encoding="utf-8"))
    except Exception:return {}
def _save(data):
    p=_settings_path();t=p.with_suffix(".tmp");t.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def _fmt(v):
    a=float(v)
    for u in ("B","KB","MB","GB"):
        if a<1024 or u=="GB":return ("%.0f %s" if u=="B" else "%.1f %s")%(a,u)
        a/=1024
def run_diagnostics(output_path=None):
    lines=["PortBridge Legacy diagnostics"]
    try:
        import tkinter,pyvisa
        lines += ["status=ok","python="+platform.python_version(),"platform="+platform.platform(),"frozen="+str(bool(getattr(sys,"frozen",False))),"tk="+str(tkinter.TkVersion),"pyvisa="+getattr(pyvisa,"__version__","unknown"),"tcp_bridge="+TcpBridgeServer.__name__,"visa_bridge="+VisaBridgeServer.__name__];status=0
    except Exception as e:lines += ["status=failed","error=%s: %s"%(type(e).__name__,e)];status=1
    text="\n".join(lines)+"\n"
    if output_path:Path(output_path).write_text(text,encoding="utf-8")
    elif sys.stdout:sys.stdout.write(text)
    return status

class App:
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk,messagebox
        self.tk,self.ttk,self.msg=tk,ttk,messagebox;self.root=tk.Tk();self.root.title("PortBridge - Legacy");self.root.geometry("820x680");self.root.minsize(760,620)
        self.bridge=None;self.events=queue.Queue();self.s=_load()
        V=tk.StringVar
        self.mode=V(value=self.s.get("mode","USB / VISA"));self.lhost=V(value=self.s.get("listen_host","0.0.0.0"));self.lport=V(value=str(self.s.get("listen_port",15026)));self.timeout=V(value=str(self.s.get("timeout_ms",5000)))
        self.rhost=V(value=self.s.get("remote_host","127.0.0.1"));self.rport=V(value=str(self.s.get("remote_port",5025)));self.resource=V(value=self.s.get("visa_resource",""));self.backend=V(value=self.s.get("visa_backend",""))
        self.status=V(value="已停止");self.client=V(value="-");self.traffic=V(value="RX 0 B / TX 0 B");self.duration=V(value="-")
        self.build();self.mode_changed();self.root.protocol("WM_DELETE_WINDOW",self.close);self.root.after(100,self.poll);self.root.after(500,self.refresh)
    def build(self):
        t=self.ttk;o=t.Frame(self.root,padding=12);o.pack(fill="both",expand=True)
        t.Label(o,text="PortBridge / Legacy",font=("Segoe UI",15,"bold")).pack(anchor="w");t.Label(o,text="老款 Windows/FSW 兼容版：无 Qt 依赖，支持 TCP→TCP 与 USB/VISA→TCP。",wraplength=760).pack(anchor="w",pady=(4,10))
        c=t.LabelFrame(o,text="桥接配置",padding=10);c.pack(fill="x");c.columnconfigure(1,weight=1)
        self.combo=t.Combobox(c,textvariable=self.mode,values=("Network / TCP","USB / VISA"),state="readonly");self.combo.bind("<<ComboboxSelected>>",lambda e:self.mode_changed())
        for row,(label,w) in enumerate([("连接类型",self.combo),("本地监听地址",t.Entry(c,textvariable=self.lhost)),("本地监听端口",t.Entry(c,textvariable=self.lport)),("超时 (ms)",t.Entry(c,textvariable=self.timeout))]):t.Label(c,text=label).grid(row=row,column=0,sticky="w",pady=4);w.grid(row=row,column=1,sticky="ew",pady=4)
        self.net=t.LabelFrame(o,text="Network / TCP",padding=10);self.net.columnconfigure(1,weight=1);t.Label(self.net,text="目标 IP / 主机名").grid(row=0,column=0,sticky="w");t.Entry(self.net,textvariable=self.rhost).grid(row=0,column=1,sticky="ew");t.Label(self.net,text="目标端口").grid(row=1,column=0,sticky="w");t.Entry(self.net,textvariable=self.rport).grid(row=1,column=1,sticky="ew")
        self.visa=t.LabelFrame(o,text="USB / VISA",padding=10);self.visa.columnconfigure(1,weight=1);t.Label(self.visa,text="VISA Resource").grid(row=0,column=0,sticky="w");rr=t.Frame(self.visa);rr.grid(row=0,column=1,sticky="ew");rr.columnconfigure(0,weight=1);self.rc=t.Combobox(rr,textvariable=self.resource);self.rc.grid(row=0,column=0,sticky="ew");self.scan=t.Button(rr,text="扫描 VISA",command=self.scan_visa);self.scan.grid(row=0,column=1);t.Label(self.visa,text="VISA Backend").grid(row=1,column=0,sticky="w");t.Entry(self.visa,textvariable=self.backend).grid(row=1,column=1,sticky="ew")
        a=t.Frame(o);a.pack(fill="x",pady=10);self.test=t.Button(a,text="连接测试 (*IDN?)",command=self.test_conn);self.start=t.Button(a,text="启动转发",command=self.start_bridge);self.stop=t.Button(a,text="停止",command=self.stop_bridge,state="disabled");self.test.pack(side="left");self.start.pack(side="left",padx=8);self.stop.pack(side="left")
        self.actions=a;sb=t.LabelFrame(o,text="运行状态",padding=10);sb.pack(fill="x")
        for i,(l,v) in enumerate([("状态",self.status),("客户端",self.client),("流量",self.traffic),("连接时长",self.duration)]):t.Label(sb,text=l).grid(row=i,column=0,sticky="w");t.Label(sb,textvariable=v).grid(row=i,column=1,sticky="w")
        lb=t.LabelFrame(o,text="日志",padding=8);lb.pack(fill="both",expand=True,pady=(10,0));self.logbox=self.tk.Text(lb,height=12,state="disabled");self.logbox.pack(fill="both",expand=True)
    def mode_changed(self):
        self.net.pack_forget();self.visa.pack_forget()
        (self.net if self.mode.get()=="Network / TCP" else self.visa).pack(fill="x",pady=(10,0),before=self.actions)
        if self.mode.get()=="Network / TCP" and self.lport.get() in ("","15026"):self.lport.set(str(self.s.get("network_listen_port",15025)))
        if self.mode.get()=="USB / VISA" and self.lport.get() in ("","15025"):self.lport.set(str(self.s.get("usb_listen_port",15026)))
    def intval(self,v,label,lo,hi):
        try:n=int(v)
        except ValueError:raise ValueError(label+" 必须是整数")
        if not lo<=n<=hi:raise ValueError("%s 必须在 %d..%d"%(label,lo,hi))
        return n
    def qlog(self,m):self.events.put(("log",m))
    def append(self,m):
        self.logbox.configure(state="normal");self.logbox.insert("end","[%s] %s\n"%(datetime.now().strftime("%H:%M:%S"),m));self.logbox.see("end");self.logbox.configure(state="disabled")
    def scan_visa(self):
        self.scan.configure(state="disabled")
        def w():
            try:self.events.put(("scan",True,list_visa_resources(self.backend.get().strip() or None)))
            except Exception as e:self.events.put(("scan",False,str(e)))
        threading.Thread(target=w,daemon=True).start()
    def test_conn(self):
        self.test.configure(state="disabled");mode=self.mode.get()
        def w():
            try:
                tm=self.intval(self.timeout.get(),"超时",100,120000)
                if mode=="Network / TCP":r=test_tcp_endpoint(self.rhost.get().strip(),self.intval(self.rport.get(),"目标端口",1,65535),tm/1000)
                else:r=test_visa_endpoint(self.resource.get().strip(),tm,self.backend.get().strip() or None)
                self.events.put(("test",True,r or "连接成功，但返回为空"))
            except Exception as e:self.events.put(("test",False,str(e)))
        threading.Thread(target=w,daemon=True).start()
    def start_bridge(self):
        try:
            lp=self.intval(self.lport.get(),"本地监听端口",1,65535);tm=self.intval(self.timeout.get(),"超时",100,120000)
            if self.mode.get()=="Network / TCP":b=TcpBridgeServer(TcpBridgeConfig(self.lhost.get().strip(),lp,self.rhost.get().strip(),self.intval(self.rport.get(),"目标端口",1,65535),tm/1000),on_event=self.qlog)
            else:b=VisaBridgeServer(VisaBridgeConfig(self.resource.get().strip(),self.lhost.get().strip(),lp,tm,backend=self.backend.get().strip() or None),on_event=self.qlog)
            b.start();self.bridge=b;self.status.set("运行中");self.start.configure(state="disabled");self.stop.configure(state="normal");self.combo.configure(state="disabled");self.save()
        except Exception as e:self.msg.showerror("启动失败",str(e))
    def stop_bridge(self):
        if self.bridge:
            try:self.bridge.stop()
            except Exception as e:self.append("停止错误: "+str(e))
        self.bridge=None;self.status.set("已停止");self.client.set("-");self.duration.set("-");self.start.configure(state="normal");self.stop.configure(state="disabled");self.combo.configure(state="readonly")
    def poll(self):
        while True:
            try:e=self.events.get_nowait()
            except queue.Empty:break
            if e[0]=="log":self.append(e[1])
            elif e[0]=="scan":
                self.scan.configure(state="normal")
                if e[1]:self.rc["values"]=e[2];self.append("扫描到 %d 个 VISA 资源"%len(e[2]))
                else:self.msg.showwarning("VISA 扫描失败",e[2])
            elif e[0]=="test":
                self.test.configure(state="normal");(self.msg.showinfo if e[1] else self.msg.showwarning)("连接测试",e[2])
        self.root.after(100,self.poll)
    def refresh(self):
        if self.bridge:
            s=self.bridge.snapshot();self.client.set(s.client_address or "等待客户端");self.traffic.set("RX %s / TX %s"%(_fmt(s.bytes_from_client),_fmt(s.bytes_to_client)))
            if s.connected_seconds is not None:
                n=int(s.connected_seconds);self.duration.set("%02d:%02d:%02d"%(n//3600,(n%3600)//60,n%60))
        self.root.after(500,self.refresh)
    def save(self):
        d={"mode":self.mode.get(),"listen_host":self.lhost.get(),"listen_port":int(self.lport.get()),"timeout_ms":int(self.timeout.get()),"remote_host":self.rhost.get(),"remote_port":int(self.rport.get()),"visa_resource":self.resource.get(),"visa_backend":self.backend.get(),"network_listen_port":self.s.get("network_listen_port",15025),"usb_listen_port":self.s.get("usb_listen_port",15026)}
        d["network_listen_port" if self.mode.get()=="Network / TCP" else "usb_listen_port"]=d["listen_port"];self.s=d;_save(d)
    def close(self):
        try:self.save()
        finally:self.stop_bridge();self.root.destroy()
    def run(self):self.root.mainloop();return 0

def main():
    p=argparse.ArgumentParser();p.add_argument("--diagnostics",action="store_true");p.add_argument("--diagnostics-file");a=p.parse_args()
    if a.diagnostics or a.diagnostics_file:return run_diagnostics(a.diagnostics_file)
    return App().run()
if __name__=="__main__":raise SystemExit(main())
