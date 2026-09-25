"""Tiny frame-driven timers for game logic."""
class Timer:
    __slots__=("duration","remaining","callback","repeat","cancelled")
    def __init__(self,duration,callback=None,repeat=False):
        self.duration=max(0.0,float(duration)); self.remaining=self.duration; self.callback=callback; self.repeat=bool(repeat); self.cancelled=False
    @property
    def done(self): return self.cancelled or (not self.repeat and self.remaining<=0)
    def cancel(self): self.cancelled=True; return self
    def reset(self): self.remaining=self.duration; self.cancelled=False; return self
    def update(self,dt):
        if self.cancelled: return
        self.remaining-=float(dt)
        while self.remaining<=0 and not self.cancelled:
            if self.callback: self.callback()
            if self.repeat and self.duration>0: self.remaining+=self.duration
            else: self.cancelled=True
_timers=[]
def _add(t): _timers.append(t); return t
def after(seconds,callback): return _add(Timer(seconds,callback))
def every(seconds,callback): return _add(Timer(seconds,callback,True))
def cancel(timer):
    timer.cancel()
    if timer in _timers: _timers.remove(timer)
def update(dt):
    for timer in tuple(_timers):
        timer.update(dt)
        if timer.done: _timers.remove(timer)
