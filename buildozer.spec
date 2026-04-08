[app]

# ── Application metadata ──────────────────────────────────────────────────────
title = NSE Analyzer
package.name = nseanalyzer
package.domain = com.nseanalyzer
version = 1.0.0

# ── Source configuration ──────────────────────────────────────────────────────
# Run `buildozer android debug` from the repository root.
# main.py (this directory) is the Kivy entry point.
source.dir = .
source.include_exts = py,html,css,js,json,txt,png,jpg,jpeg,gif,svg,ico,kv,atlas,xml

# Exclude everything except the niftytrader app and this entry point
source.exclude_dirs =
    .git,
    .github,
    AutoTradeNSE,
    Trading_dashboard_nse,
    Znifty_fine_dashboard,
    Znifty_Midcap_fine_dashboard,
    android/.buildozer,
    android/bin,
    __pycache__,
    .venv,
    venv,
    env,
    .buildozer,
    bin

# Kivy garden extensions (provides in-app WebView widget)
garden_requirements = webview

# ── Python / pip requirements bundled into the APK ───────────────────────────
# python-for-android provides numpy / pandas / scipy via built-in recipes.
requirements =
    python3==3.11.8,
    kivy==2.3.0,
    flask==2.3.3,
    flask_socketio==5.3.4,
    requests==2.31.0,
    numpy,
    pandas,
    scipy,
    python-dotenv==1.0.0,
    bidict,
    simple-websocket,
    Werkzeug,
    click,
    Jinja2,
    MarkupSafe,
    itsdangerous,
    charset-normalizer,
    certifi,
    idna,
    urllib3

# ── Icons & splash ────────────────────────────────────────────────────────────
# Uncomment and provide image files to customise:
# icon.filename = %(source.dir)s/niftytrader/niftytrader/static/favicon.ico
# presplash.filename = %(source.dir)s/android/presplash.png

# ── Orientation ───────────────────────────────────────────────────────────────
orientation = portrait

# ── Buildozer settings ────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1

# ── Android-specific settings ─────────────────────────────────────────────────
[app:android]

# Target / minimum API levels
android.api = 33
android.minapi = 21

# SDK / NDK versions (downloaded automatically on first build)
android.sdk = 33
android.ndk = 25b

# Build architecture – arm64-v8a covers all modern Android phones.
# Add armeabi-v7a for older 32-bit devices (increases build time & APK size).
android.archs = arm64-v8a

# Required permissions
android.permissions =
    INTERNET,
    ACCESS_NETWORK_STATE,
    ACCESS_WIFI_STATE

# Network security config – allows cleartext HTTP to localhost (127.0.0.1)
# so the in-app WebView can reach the Flask server.
android.manifest.application_arguments = android:networkSecurityConfig="@xml/network_security_config"

# Bootstrap (sdl2 is the standard Kivy bootstrap)
android.bootstrap = sdl2

# Gradle dependencies
android.gradle_dependencies = androidx.webkit:webkit:1.7.0

# Release signing – leave blank for debug builds.
# Uncomment and fill in for a signed release APK:
# android.keystore = /path/to/release.keystore
# android.keystore_alias = nseanalyzer
# android.keystore_password = <password>
# android.keyalias_password = <password>

# ── iOS (not targeted) ────────────────────────────────────────────────────────
[app:ios]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0
