"""
NSE Analyzer – Android / Kivy Entry Point
==========================================
This file is the entry point used by Buildozer when packaging the app as an
Android APK.  It starts the NiftyTrader Flask server in a background thread
and then displays the dashboard inside an Android WebView.

Desktop fallback: opens the dashboard in the system default browser.

Run on desktop (for quick testing without a device):
    pip install kivy flask flask-socketio requests pandas numpy scipy python-dotenv
    python main.py
"""

import os
import sys
import threading

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NIFTYTRADER_DIR = os.path.join(ROOT_DIR, "niftytrader")

for _p in [ROOT_DIR, NIFTYTRADER_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Kivy imports ─────────────────────────────────────────────────────────────
from kivy.app import App                        # noqa: E402
from kivy.uix.boxlayout import BoxLayout        # noqa: E402
from kivy.uix.label import Label                # noqa: E402
from kivy.uix.progressbar import ProgressBar    # noqa: E402
from kivy.clock import Clock                    # noqa: E402
from kivy.utils import platform                 # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

_server_ready = threading.Event()


# ── Flask server ──────────────────────────────────────────────────────────────

def _run_flask_server():
    """Start the NiftyTrader Flask server in a daemon background thread."""
    try:
        os.chdir(NIFTYTRADER_DIR)

        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        from niftytrader import create_app, socketio  # type: ignore

        flask_app = create_app("production")
        flask_app.config["SERVER_NAME"] = None
        _server_ready.set()

        socketio.run(
            flask_app,
            host=SERVER_HOST,
            port=SERVER_PORT,
            debug=False,
            use_reloader=False,
            log_output=False,
        )
    except Exception as exc:
        print(f"[NSEAnalyzer] Flask server error: {exc}")
        _server_ready.set()  # unblock even on failure


# ── UI widgets ────────────────────────────────────────────────────────────────

class LoadingScreen(BoxLayout):
    """Shown while the Flask server is starting."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=10, **kwargs)
        self.add_widget(Label(text="NSE Analyzer", font_size="28sp", bold=True))
        self.add_widget(Label(text="Starting server…", font_size="14sp"))
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        self.add_widget(self.progress)
        self._tick = 0
        Clock.schedule_interval(self._update_progress, 0.1)

    def _update_progress(self, dt):
        self._tick += 2
        self.progress.value = min(self._tick, 90)


# ── Main application ──────────────────────────────────────────────────────────

class NSEAnalyzerApp(App):
    title = "NSE Analyzer"

    def build(self):
        self._loading = LoadingScreen()

        # Start Flask in a daemon thread so it exits when the app closes
        threading.Thread(target=_run_flask_server, daemon=True).start()

        # Poll until server is ready, then switch to WebView
        Clock.schedule_interval(self._check_server, 0.5)
        return self._loading

    # ── Server-ready callback ────────────────────────────────────────────────

    def _check_server(self, dt):
        if _server_ready.is_set():
            Clock.unschedule(self._check_server)
            # Give the server a moment to fully bind the port
            Clock.schedule_once(self._show_webview, 1.5)

    # ── WebView display ──────────────────────────────────────────────────────

    def _show_webview(self, dt):
        if platform == "android":
            self._show_android_webview()
        else:
            # Desktop: open dashboard in the default browser
            import webbrowser
            webbrowser.open(SERVER_URL)
            self._loading.clear_widgets()
            self._loading.add_widget(
                Label(
                    text=f"Dashboard opened in browser.\nURL: {SERVER_URL}",
                    font_size="14sp",
                )
            )

    def _show_android_webview(self):
        """Replace loading screen with native Android WebView."""
        try:
            # Preferred: kivy_garden.webview (in-process WebView widget)
            from kivy_garden.webview import WebView  # type: ignore

            webview = WebView(url=SERVER_URL)
            self.root_window.remove_widget(self._loading)
            self.root_window.add_widget(webview)
        except ImportError:
            # Fallback: launch the system browser via Android Intent
            try:
                from jnius import autoclass  # type: ignore

                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(SERVER_URL))
                PythonActivity.mActivity.startActivity(intent)
            except Exception as exc:
                print(f"[NSEAnalyzer] Cannot open WebView: {exc}")
                self._loading.clear_widgets()
                self._loading.add_widget(
                    Label(
                        text=f"Open your browser and go to:\n{SERVER_URL}",
                        font_size="14sp",
                    )
                )


if __name__ == "__main__":
    NSEAnalyzerApp().run()
