# NSE Analyzer – Android APK Build Guide

Convert the NSE Analyzer Flask web-app into a native Android APK using **Buildozer** (the standard Python-to-Android packaging tool built on top of python-for-android).

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Android APK  (built by Buildozer)                      │
│                                                         │
│  ┌───────────────┐    starts    ┌───────────────────┐  │
│  │  Kivy UI      │ ──────────▶  │  Flask server     │  │
│  │  (main.py)    │              │  (niftytrader/)   │  │
│  │               │   WebView    │  127.0.0.1:5000   │  │
│  │  WebView      │ ◀─────────── │                   │  │
│  └───────────────┘              └───────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

1. On launch, `main.py` starts the **NiftyTrader Flask server** in a background thread.  
2. A Kivy **loading screen** is shown while the server binds to port 5000.  
3. Once ready, the app switches to an **Android WebView** pointed at `http://127.0.0.1:5000`.  
4. The user interacts with the full NSE Analyzer dashboard without leaving the app.

---

## Automated Build via GitHub Actions (Recommended)

Every push to `main` / `master` automatically builds a **debug APK** and uploads it as a downloadable artifact.

### Download the APK

1. Go to the repository on GitHub → **Actions** tab.  
2. Click the latest **"Build Android APK"** workflow run.  
3. Scroll to the **Artifacts** section at the bottom.  
4. Download **`NSEAnalyzer-debug-apk`** (a `.zip` containing the `.apk` file).

> **Note:** Debug APKs are signed with a debug key and are suitable for testing. For a release version see [Building a Release APK](#building-a-release-apk) below.

---

## Manual Build (Local Machine)

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Ubuntu 22.04 / 20.04 | — | Windows/macOS users: use WSL2 or Docker |
| Python | 3.10 | `pyenv` recommended |
| Java JDK | 17 | `sudo apt install openjdk-17-jdk` |
| Buildozer | ≥ 1.5 | `pip install buildozer` |
| Cython | latest | `pip install cython` |
| Android SDK | 33 | downloaded automatically by Buildozer |
| Android NDK | 25b | downloaded automatically by Buildozer |

### Step-by-step

```bash
# 1. Clone the repository (or use your existing clone)
git clone https://github.com/<your-org>/NSEAnalyzer.git
cd NSEAnalyzer

# 2. Install system build dependencies
sudo apt-get update && sudo apt-get install -y \
  build-essential autoconf libtool libltdl-dev \
  python3-dev libffi-dev libssl-dev zlib1g-dev \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
  cmake ninja-build ccache git zip unzip

# 3. Install Python build tools
pip install --upgrade pip
pip install buildozer cython virtualenv

# 4. Build the debug APK  (first build downloads ~1 GB of SDK/NDK – be patient)
buildozer android debug

# 5. The APK is placed in:
#    bin/nseanalyzer-1.0.0-arm64-v8a-debug.apk
```

### Install on your Android device

```bash
# Option A – adb (USB debugging must be enabled on the device)
adb install bin/nseanalyzer-*.apk

# Option B – copy the APK to your device and open it in a file manager
# (enable "Install from unknown sources" in Android Settings first)
```

---

## Building a Release APK

1. **Generate a keystore** (one-time):

   ```bash
   keytool -genkey -v -keystore nse_release.keystore \
     -alias nseanalyzer -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Uncomment and fill in** the signing section in `buildozer.spec`:

   ```ini
   android.keystore = /path/to/nse_release.keystore
   android.keystore_alias = nseanalyzer
   android.keystore_password = <your-password>
   android.keyalias_password = <your-password>
   ```

3. **Build a release APK**:

   ```bash
   buildozer android release
   ```

   The signed APK will be at `bin/nseanalyzer-1.0.0-arm64-v8a-release.apk`.

---

## Project Structure (Android-related files)

```
NSEAnalyzer/
├── main.py                            ← Kivy entry point (WebView + Flask launcher)
├── buildozer.spec                     ← Buildozer build configuration
├── android/
│   └── res/
│       └── xml/
│           └── network_security_config.xml  ← Allows HTTP to localhost
├── .github/
│   └── workflows/
│       └── build-apk.yml              ← GitHub Actions CI workflow
└── niftytrader/                       ← Flask application (bundled into the APK)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `SDK/NDK download timeout` | Re-run `buildozer android debug`; cached after first download |
| `BUILD FAILED` on first run | Check `build.log`; usually a missing system library |
| App crashes on launch | Enable ADB logcat: `adb logcat \| grep python` |
| Blank screen / WebView not loading | Ensure `android/res/xml/network_security_config.xml` is present |
| `kivy_garden.webview` not found | The app falls back to the system browser; install the garden package |
| Very large APK size | Reduce `requirements` in `buildozer.spec`; split into ABI-specific APKs |

---

## Device Requirements

- Android 5.0 (API 21) or higher  
- ~150 MB free storage (first launch extracts assets)  
- Internet access for live NSE data

---

## Notes

- The APK bundles a **complete Python interpreter** and all dependencies — no internet connection is required to *run* the app (only for fetching live market data from NSE).  
- First launch may take **10–20 seconds** while Python assets are extracted.  
- Tested architectures: `arm64-v8a` (most modern phones). Add `armeabi-v7a` to `android.archs` in `buildozer.spec` for older 32-bit devices (increases build time and APK size).
