from __future__ import annotations

import functools
import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--enable-gpu-rasterization --enable-zero-copy",
)

from PyQt6.QtCore import QObject, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pypresence import Presence

from mod_api import ModManager, SaveStore


APP_DIR = Path(__file__).resolve().parent
SAVE_DIR = APP_DIR / "saves"
MODS_DIR = APP_DIR / "mods"
APP_ICON = APP_DIR / "ico.png"
APP_NAME = "FNAF3 WINT MODS remix"
DISCORD_CLIENT_ID = "1568717580913483957"
GAME_PORT = 18765
REQUIRED_FILES = (
    APP_ICON,
    APP_DIR / "index.html",
    APP_DIR / "src" / "Runtime.js",
    APP_DIR / "src" / "RuntimeExtensions.js",
    APP_DIR / "resources" / "fnaf 3.cch",
    APP_DIR / "resources" / "fnaf 3.cc1",
)


class GameRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        request_path = unquote(urlsplit(self.path).path)
        if request_path.lower().startswith("/mods/") and (
            request_path.lower().endswith(".py")
            or Path(request_path).name.lower() == "mod.json"
        ):
            self.send_error(404, "Los archivos de código y manifiesto de mods no se publican.")
            return

        if request_path == "/resources/manifest.json":
            audio_files = sorted(
                path.relative_to(APP_DIR).as_posix()
                for path in (APP_DIR / "resources").glob("*.mp3")
                if path.is_file()
            )
            payload = json.dumps(audio_files).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return

        super().do_GET()

    def end_headers(self) -> None:
        if self.path.partition("?")[0].lower().endswith(".mp3"):
            self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()

    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


class DiscordPresence:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="discord-rich-presence",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            rpc = Presence(
                DISCORD_CLIENT_ID,
                connection_timeout=5,
                response_timeout=5,
            )
            connected = False
            started_at = int(time.time())
            try:
                rpc.connect()
                connected = True
                while not self._stop_event.is_set():
                    rpc.update(
                        details=APP_NAME,
                        state="Jugando",
                        start=started_at,
                    )
                    self._stop_event.wait(15)
            except Exception as error:
                print(
                    f"Discord Rich Presence no disponible; se reintentará: {error}",
                    file=sys.stderr,
                )
                self._stop_event.wait(15)
            finally:
                if connected:
                    try:
                        rpc.clear()
                        rpc.close()
                    except Exception as error:
                        print(
                            f"No se pudo cerrar la conexión de Discord: {error}",
                            file=sys.stderr,
                        )


class LocalGameServer:
    def __init__(self) -> None:
        handler = functools.partial(GameRequestHandler, directory=str(APP_DIR))
        self._server = ThreadingHTTPServer(("127.0.0.1", GAME_PORT), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="fnaf3-local-server",
            daemon=True,
        )
        self._thread.start()

    @property
    def game_url(self) -> QUrl:
        return QUrl(f"http://127.0.0.1:{GAME_PORT}/index.html")

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


class GameBridge(QObject):
    browser_event = pyqtSignal(str, str)

    def __init__(self, mod_manager: ModManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mod_manager = mod_manager
        self._browser_ready = False
        self._pending_events: list[tuple[str, str]] = []
        self._mod_manager.browser_publish = self.publish

    @pyqtSlot(str, result=str)
    def execute_command(self, command_line: str) -> str:
        return json.dumps(
            {"output": self._mod_manager.execute_command(command_line)},
            ensure_ascii=False,
        )

    @pyqtSlot(str, str, result=str)
    def post_event(self, event_name: str, payload_json: str) -> str:
        try:
            payload = json.loads(payload_json)
            if event_name == "bridge.ready":
                self._browser_ready = True
                for pending_event, pending_payload in self._pending_events:
                    self.browser_event.emit(pending_event, pending_payload)
                self._pending_events.clear()
            else:
                self._mod_manager.emit_event(event_name, payload)
            return '{"ok":true}'
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @pyqtSlot(result=str)
    def get_mods(self) -> str:
        return json.dumps(
            {
                "mods": list(self._mod_manager.mods.values()),
                "errors": self._mod_manager.errors,
            },
            ensure_ascii=False,
        )

    @pyqtSlot(result=str)
    def get_content(self) -> str:
        return json.dumps(self._mod_manager.get_content(), ensure_ascii=False)

    @pyqtSlot(result=str)
    def get_client_mods(self) -> str:
        client_mods = [
            {"id": mod["id"], "name": mod["name"], "url": mod["client_url"]}
            for mod in self._mod_manager.mods.values()
            if mod["enabled"] and mod["status"] == "cargado" and "client_url" in mod
        ]
        return json.dumps(client_mods, ensure_ascii=False)

    def publish(self, event_name: str, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False)
        if self._browser_ready:
            self.browser_event.emit(event_name, serialized)
        else:
            self._pending_events.append((event_name, serialized))


class GameWindow(QMainWindow):
    def __init__(self, presence: DiscordPresence) -> None:
        super().__init__()
        self._presence = presence
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self._mods = ModManager(MODS_DIR, SaveStore(SAVE_DIR))
        self._server = LocalGameServer()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(APP_ICON)))
        self.resize(1024, 768)

        self._view = QWebEngineView(self)
        self._profile = QWebEngineProfile("FNAF3-WINT-MODS", self)
        self._profile.setPersistentStoragePath(str(SAVE_DIR / "webengine"))
        self._profile.setCachePath(str(SAVE_DIR / "cache"))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self._page = QWebEnginePage(self._profile, self._view)
        self._view.setPage(self._page)
        self._view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled,
            True,
        )
        self._view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled,
            True,
        )
        self._bridge = GameBridge(self._mods, self)
        self._channel = QWebChannel(self._page)
        self._channel.registerObject("modBridge", self._bridge)
        self._page.setWebChannel(self._channel)
        self._bridge.browser_event.connect(self._publish_browser_event)
        self.setCentralWidget(self._view)
        self._view.load(self._server.game_url)

    def _publish_browser_event(self, event_name: str, payload_json: str) -> None:
        event = json.dumps(event_name)
        payload = json.dumps(payload_json)
        self._page.runJavaScript(
            f"window.FNAF3 && window.FNAF3.receive({event}, JSON.parse({payload}));"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        self._presence.stop()
        self._server.close()
        super().closeEvent(event)


def main() -> int:
    QGuiApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
        True,
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setWindowIcon(QIcon(str(APP_ICON)))

    missing_files = [path for path in REQUIRED_FILES if not path.is_file()]
    if missing_files:
        missing_list = "\n".join(str(path) for path in missing_files)
        QMessageBox.critical(
            None,
            "Archivos del juego no encontrados",
            f"No se puede iniciar el juego. Faltan estos archivos:\n\n{missing_list}",
        )
        return 1

    try:
        presence = DiscordPresence()
        window = GameWindow(presence)
    except OSError as error:
        QMessageBox.critical(
            None,
            "No se pudo preparar el juego",
            f"El launcher no pudo preparar el servidor local, los guardados o los mods:\n{error}",
        )
        return 1

    presence.start()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
