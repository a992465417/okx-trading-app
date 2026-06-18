#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OKX 交易引擎 — 带 callback 通知，供 Kivy GUI 调用"""
import hashlib, hmac, base64, time, json, sys, os, traceback, threading
from datetime import datetime, timezone
import requests as _req

DEFAULT_CFG = {
    "ak": "", "as": "", "ap": "", "sim": True,
    "sym": "ETH-USDT-SWAP", "lv": 100, "mm": "cross", "bp": 0.01,
    "min_sz": 0.01, "t": [0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0],
    "mh": 10, "interval": 0.1, "tp_r": 0.35, "ttp": 0.50,
    "tsl": -1.0, "ssl": 4.40, "to": 10, "mr": 3,
}
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "okx_config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: return json.load(f)
        except: pass
    return dict(DEFAULT_CFG)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f: json.dump(cfg, f, indent=2)

class OKXBot:
    def __init__(self, config=None, on_log=None, on_status=None):
        self.cfg = config or dict(DEFAULT_CFG)
        self.on_log = on_log; self.on_status = on_status
        self._stop = False; self._thread = None
        self._se = _req.Session(); self._se.headers.update({"Content-Type": "application/json"})
        self.lf = self.sf = 0; self.hlb = self.hsb = False
        self.tcp = 0.0; self.running = False

    def _ts(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"
    def _sign(self,t,m,p,b):
        return base64.b64encode(hmac.new(self.cfg["as"].encode(),(t+m.upper()+p+b).encode(),hashlib.sha256).digest()).decode()

    def _api(self,method,path,params=None,data=None):
        body = json.dumps(data,separators=(",",":")) if data else ""
        url = f"https://www.okx.com{path}"; rp = path
        if params and method.upper()=="GET":
            qs = "&".join(f"{k}={v}" for k,v in params.items())
            url+="?"+qs; rp+="?"+qs
        t = self._ts()
        hd = {"OK-ACCESS-KEY":self.cfg["ak"],"OK-ACCESS-SIGN":self._sign(t,method,rp,body),
              "OK-ACCESS-TIMESTAMP":t,"OK-ACCESS-PASSPHRASE":self.cfg["ap"]}
        if self.cfg["sim"]: hd["x-simulated-trading"]="1"
        for a in range(self.cfg["mr"]):
            try:
                r = (self._se.get if method.upper()=="GET" else self._se.post)(url,headers=hd,data=body,timeout=self.cfg["to"])
                if r.status_code==429: time.sleep(.5); continue
                if r.status_code!=200:
                    if a<self.cfg["mr"]-1: time.sleep(.3); continue
                    return None
                j = r.json()
                if j.get("code")=="0": return j
                if j.get("code","") in ("500","504","50104","50120"):
                    if a<self.cfg["mr"]-1: time.sleep(.3); continue
                return None
            except:
                if a<self.cfg["mr"]-1: time.sleep(.5); continue
        return None

    def _get_pos(self):
        tkr = self._api("GET","/api/v5/market/ticker",params={"instId":self.cfg["sym"]})
        cp = float(tkr["data"][0].get("last",0)) if tkr and tkr.get("data") else None
        r = self._api("GET","/api/v5/account/positions",params={"instId":self.cfg["sym"]})
        lp={"sz":0.0,"px":0.0,"upl":0.0}; sp={"sz":0.0,"px":0.0,"upl":0.0}
        if r:
            for p in r.get("data",[]):
                if p.get("instId")!=self.cfg["sym"]: continue
                sz=float(p.get("pos",0) or 0)
                if sz<=0: continue
                px=float(p.get("avgPx",0) or 0); up=float(p.get("upl",0) or 0); s=p.get("posSide")
                if s=="long": lp={"sz":sz,"px":px,"upl":up}
                elif s=="short": sp={"sz":sz,"px":px,"upl":up}
        return lp,sp,cp

    def _log(self,msg):
        if self.on_log: self.on_log(msg)

    def _close_all(self):
        self._log("🔴 全平"); self._close_side("short"); time.sleep(.2); self._close_side("long")
        self.lf=self.sf=0; self.hlb=self.hsb=False

    def _close_side(self,side):
        lp,sp,_=self._get_pos(); pos=lp if side=="long" else sp
        if pos["sz"]<=0: return 0.0
        cs="sell" if side=="long" else "buy"
        upl=pos["upl"]
        r=self._api("POST","/api/v5/trade/order",data={"instId":self.cfg["sym"],"tdMode":"cross","side":cs,"posSide":side,"ordType":"market","sz":str(round(pos["sz"],2))})
        if r: self.tcp+=upl; self._log(f"✅ 平{side} {pos['sz']}张 UPL:{upl:+.2f}")
        return upl if r else 0.0

    def start(self):
        self._stop=False; self._thread=threading.Thread(target=self._run,daemon=True); self._thread.start()
    def stop(self):
        self._stop=True; self._log("⏹ 停止引擎")
    def close_all(self):
        self._close_all()
    def is_running(self):
        return self.running and self._thread and self._thread.is_alive()

    def _run(self):
        self.running=True; self._log("🚀 OKX Bot 启动")
        while not self._stop:
            try:
                lp,sp,cp=self._get_pos()
                if cp and self.on_status:
                    self.on_status({"price":cp,"long_sz":lp["sz"],"short_sz":sp["sz"],"running":True})
            except Exception as e:
                self._log(f"❌ {e}")
            time.sleep(self.cfg["interval"])
        self.running=False
