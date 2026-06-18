#!/usr/bin/env python3
import os
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_ORIENTATION"] = "portrait"

import kivy
kivy.require("2.0.0")
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from okx_bot import OKXBot, load_config, save_config

class MainScreen(Screen):
    pass

class ConfigScreen(Screen):
    def on_enter(self):
        cfg = load_config()
        self.ids.txt_ak.text = cfg.get("ak","")
        self.ids.txt_as.text = cfg.get("as","")
        self.ids.txt_ap.text = cfg.get("ap","")
        self.ids.txt_sym.text = cfg.get("sym","ETH-USDT-SWAP")
        self.ids.txt_lv.text = str(cfg.get("lv",100))
        self.ids.txt_bp.text = str(cfg.get("bp",0.01))

class OKXApp(App):
    def build(self):
        self.title = "OKX交易机器人"
        self.bot = OKXBot(config=load_config(), on_log=self.log, on_status=self.status)
        sm = ScreenManager()
        sm.add_widget(ConfigScreen(name="config"))
        sm.add_widget(MainScreen(name="main"))
        sm.current = "main"
        self._log_buf = []
        Clock.schedule_interval(self._update, 0.2)
        return sm

    def log(self, msg):
        self._log_buf.append(msg)
    def status(self, s):
        self._status = s
    def _update(self, dt):
        ms = self.root.get_screen("main") if self.root else None
        if not ms: return
        if self._log_buf:
            ms.ids.lbl_log.text = "\n".join(self._log_buf[-50:])
            self._log_buf.clear()
        if hasattr(self,"_status") and self._status:
            s = self._status
            ms.ids.lbl_price.text = f"${s.get('price',0):.2f}"
            ms.ids.lbl_long.text = f"持仓: {s.get('long_sz',0):.3f}张"
            ms.ids.lbl_short.text = f"持仓: {s.get('short_sz',0):.3f}张"

    def toggle_bot(self):
        if self.bot.is_running(): self.bot.stop()
        else: self.bot.start()

    def save_and_start(self):
        cs = self.root.get_screen("config")
        cfg = load_config()
        cfg["ak"] = cs.ids.txt_ak.text.strip()
        cfg["as"] = cs.ids.txt_as.text.strip()
        cfg["ap"] = cs.ids.txt_ap.text.strip()
        cfg["sym"] = cs.ids.txt_sym.text.strip()
        try:
            cfg["lv"] = int(cs.ids.txt_lv.text)
            cfg["bp"] = float(cs.ids.txt_bp.text)
        except: pass
        save_config(cfg)
        self.bot.update_config(cfg)
        self.root.current = "main"
        if not self.bot.is_running(): self.bot.start()

    def close_all(self): self.bot.close_all()
    def switch_to_config(self):
        if self.bot.is_running(): self.bot.stop()
        self.root.get_screen("config").on_enter()
        self.root.current = "config"
    def exit_app(self):
        if self.bot.is_running(): self.bot.stop()
        self.stop(); os._exit(0)

if __name__ == "__main__":
    OKXApp().run()
