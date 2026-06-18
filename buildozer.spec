# Buildozer spec for OKX Trading Bot APK
[app]
title = OKX交易机器人
package.name = okxtrader
package.domain = com.okx.trader
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy,requests
android.archs = arm64-v8a
android.api = 35
android.minapi = 26
android.ndk = 27
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.accept_sdk_license = True
android.fullscreen = 0
android.allow_backup = 1
android.orientation = portrait
android.debug = 1
android.gstreamer = 0
android.private_storage = 0
android.presplash_color = "#1E1E22"
android.presplash_fill_width = 0
android.export_path = ./bin/
[buildozer]
log_level = 2
warn_on_root = 1
