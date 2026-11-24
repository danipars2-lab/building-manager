[app]
title = Modiriat Houshmand Sakhteman
package.name = buildingmanager
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf,db
version = 0.1.0
requirements = python3,kivy,openpyxl
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
[buildozer]
log_level = 2
warn_on_root = 1
