"""Tkinter fallback for old Windows systems."""
import tkinter as tk
from tkinter import ttk,messagebox
from .core import TcpBridgeConfig,TcpBridgeServer

def main():
    root=tk.Tk();root.title("PortBridge Legacy");root.geometry("560x360")
    bridge=[None]
    host=tk.StringVar(value="0.0.0.0");port=tk.StringVar(value="15025");remote=tk.StringVar(value="192.168.1.100");rport=tk.StringVar(value="5025");status=tk.StringVar(value="Stopped")
    f=ttk.Frame(root,padding=16);f.pack(fill="both",expand=True)
    for i,(label,var) in enumerate([("Listen address",host),("Listen port",port),("Target host",remote),("Target port",rport)]):
        ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=5);ttk.Entry(f,textvariable=var,width=38).grid(row=i,column=1,sticky="ew",pady=5)
    ttk.Label(f,textvariable=status).grid(row=4,column=0,columnspan=2,pady=10)
    def start():
        try:
            b=TcpBridgeServer(TcpBridgeConfig(host.get(),int(port.get()),remote.get(),int(rport.get())));b.start();bridge[0]=b;status.set("Running")
        except Exception as e:messagebox.showerror("Start failed",str(e))
    def stop():
        if bridge[0]:bridge[0].stop();bridge[0]=None
        status.set("Stopped")
    ttk.Button(f,text="Start",command=start).grid(row=5,column=0);ttk.Button(f,text="Stop",command=stop).grid(row=5,column=1)
    root.protocol("WM_DELETE_WINDOW",lambda:(stop(),root.destroy()));root.mainloop();return 0
