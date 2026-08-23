[app]

# (str) Title of your application
title = Aqsaty

# (str) Package name
package.name = aqsaty

# (str) Package domain (needed for android/ios packaging)
package.domain = org.aqsaty

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (python files, databases, etc.)
source.include_exts = py,png,jpg,kv,atlas,db

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,pillow,sqlite3

# (str) Supported orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

# (str) python-for-android git socket branch to use
p4a.branch = master

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
