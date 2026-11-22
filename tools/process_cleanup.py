"""Cleanup helper for smoke tests, including simulator launcher grandchildren."""
from pathlib import Path
import os
import signal
import time

def _snapshot():
    found={}
    for p in Path('/proc').glob('[0-9]*/stat'):
        try:
            text=p.read_text();fields=text[text.rfind(')')+2:].split()
            found[int(p.parent.name)]=(int(fields[1]),fields[19])
        except (OSError,ValueError,IndexError):pass
    return found

def stop_tree(process):
    table=_snapshot();descendants={process.pid}
    while True:
        more={pid for pid,(parent,_) in table.items() if parent in descendants}
        if more<=descendants:break
        descendants|=more
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:process.wait(timeout=9)
        except Exception:pass
    # Verify start identity before signalling a PID that might have exited.
    for sig in (signal.SIGTERM,signal.SIGKILL):
        current=_snapshot()
        for pid in descendants:
            if pid in current and pid in table and current[pid][1]==table[pid][1]:
                try:os.kill(pid,sig)
                except ProcessLookupError:pass
        time.sleep(.1)
    if process.poll() is None:process.wait(timeout=2)
