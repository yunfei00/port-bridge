import argparse

def main():
    parser=argparse.ArgumentParser(description="PortBridge")
    parser.add_argument("--legacy",action="store_true",help="Use Tkinter legacy UI")
    args=parser.parse_args()
    if args.legacy:
        from .legacy import main as run
    else:
        from .gui import run_gui as run
    return run()

if __name__=="__main__":
    raise SystemExit(main())
