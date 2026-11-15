from __future__ import annotations

import importlib.util
import json
import math
import re
import shlex
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_EVENT_NAME = re.compile(r"^[a-zA-Z0-9_.:-]+$")


class SaveStore:
    def __init__(self, save_dir: Path) -> None:
        self.root = save_dir / "mods"
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def get(self, mod_id: str, key: str, default: Any = None) -> Any:
        data = self._read(mod_id)
        return data.get(key, default)

    def set(self, mod_id: str, key: str, value: Any) -> None:
        self._validate_mod_id(mod_id)
        if not key:
            raise ValueError("La clave del dato no puede estar vacía.")
        with self._lock:
            data = self._read(mod_id)
            data[key] = value
            path = self.root / f"{mod_id}.json"
            temporary_path = path.with_suffix(".json.tmp")
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False),
                encoding="utf-8",
            )
            temporary_path.replace(path)

    def _read(self, mod_id: str) -> dict[str, Any]:
        self._validate_mod_id(mod_id)
        path = self.root / f"{mod_id}.json"
        with self._lock:
            if not path.exists():
                return {}
            data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"El archivo de datos del mod {mod_id} debe contener un objeto JSON.")
        return data

    @staticmethod
    def _validate_mod_id(mod_id: str) -> None:
        if not _IDENTIFIER.fullmatch(mod_id):
            raise ValueError(f"Identificador de mod inválido: {mod_id!r}")


class ModAPI:
    def __init__(self, manager: ModManager, mod_id: str) -> None:
        self._manager = manager
        self.mod_id = mod_id

    def register_command(self, name: str, callback: Callable[..., Any]) -> None:
        self._manager.register_command(self.mod_id, name, callback)

    def register_animatronic(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "animatronics", definition)

    def register_phantom(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(
            self.mod_id, "animatronics", {**definition, "kind": "phantom"}
        )

    def register_system(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "systems", definition)

    def register_game_mode(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "modes", definition)

    def register_minigame(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "minigames", definition)

    def register_skin(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "skins", definition)

    def register_effect(self, definition: dict[str, Any]) -> None:
        self._manager.register_content(self.mod_id, "effects", definition)

    def on(self, event_name: str, callback: Callable[[Any], Any]) -> None:
        self._manager.register_event(self.mod_id, event_name, callback)

    def emit(self, event_name: str, payload: Any = None) -> None:
        self._manager.emit_from_mod(event_name, payload)

    def log(self, message: Any) -> None:
        self._manager.log(f"[mod:{self.mod_id}] {message}")

    def get_data(self, key: str, default: Any = None) -> Any:
        return self._manager.save_store.get(self.mod_id, key, default)

    def set_data(self, key: str, value: Any) -> None:
        self._manager.save_store.set(self.mod_id, key, value)

    def get_setting(self, key: str, default: Any = None) -> Any:
        settings = self._manager.manifests[self.mod_id].get("settings", {})
        return self.get_data(f"setting:{key}", settings.get(key, default))

    def set_setting(self, key: str, value: Any) -> None:
        self.set_data(f"setting:{key}", value)

    def asset_url(self, relative_path: str) -> str:
        return self._manager.asset_url(self.mod_id, relative_path)

    def trigger(self, event_name: str, payload: Any = None) -> None:
        self._manager.trigger_game_event(self.mod_id, event_name, payload)

    def set_camera_effect(self, effect: str, intensity: float = 1.0) -> None:
        self.trigger("camera.effect", {"effect": effect, "intensity": intensity})

    def add_map_marker(
        self,
        marker_id: str,
        label: str,
        camera: str,
        kind: str = "animatronic",
    ) -> None:
        self.trigger(
            "map.marker",
            {"id": marker_id, "label": label, "camera": camera, "kind": kind},
        )

    def remove_map_marker(self, marker_id: str) -> None:
        self.trigger("map.marker.remove", {"id": marker_id})

    def trigger_jumpscare(self, definition_id: str) -> None:
        self.trigger("jumpscare", {"id": definition_id})

    def play_audio(
        self,
        relative_path: str,
        loop: bool = False,
        sound_id: str | None = None,
        *,
        position: tuple[float, float, float] | None = None,
        volume: float = 1.0,
        spatial: bool = True,
        options: dict[str, Any] | None = None,
    ) -> None:
        asset_url = self.asset_url(relative_path)
        if Path(relative_path).suffix.lower() != ".mp3":
            raise ValueError("Los mods solo pueden cargar audio MP3.")
        if (
            not isinstance(volume, (int, float))
            or not math.isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise ValueError("volume debe estar entre 0.0 y 1.0.")
        if position is not None and (
            len(position) != 3
            or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in position
            )
        ):
            raise ValueError("position debe contener tres coordenadas numéricas (x, y, z).")
        if options is not None and not isinstance(options, dict):
            raise ValueError("options debe ser un objeto de configuración.")
        audio_options = dict(options or {})
        try:
            json.dumps(audio_options, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError("options debe contener únicamente valores JSON finitos.") from error
        self.trigger(
            "audio.play",
            {
                **audio_options,
                "src": asset_url,
                "loop": bool(loop),
                "id": sound_id or relative_path,
                "position": list(position) if position is not None else None,
                "volume": float(volume),
                "spatial": bool(spatial),
            },
        )

    def stop_audio(self, sound_id: str) -> None:
        self.trigger("audio.stop", {"id": sound_id})

    def pause_audio(self, sound_id: str) -> None:
        self.trigger("audio.pause", {"id": sound_id})

    def resume_audio(self, sound_id: str) -> None:
        self.trigger("audio.resume", {"id": sound_id})

    def set_audio_position(
        self, sound_id: str, position: tuple[float, float, float]
    ) -> None:
        if len(position) != 3 or any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in position
        ):
            raise ValueError("position debe contener tres coordenadas numéricas finitas.")
        self.trigger("audio.position", {"id": sound_id, "position": list(position)})

    def set_audio_orientation(
        self, sound_id: str, orientation: tuple[float, float, float]
    ) -> None:
        if len(orientation) != 3 or any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in orientation
        ):
            raise ValueError(
                "orientation debe contener tres coordenadas numéricas finitas."
            )
        self.trigger(
            "audio.orientation",
            {"id": sound_id, "orientation": list(orientation)},
        )

    def set_audio_volume(self, sound_id: str, volume: float) -> None:
        if (
            not isinstance(volume, (int, float))
            or not math.isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise ValueError("volume debe estar entre 0.0 y 1.0.")
        self.trigger("audio.volume", {"id": sound_id, "volume": float(volume)})

    def fade_audio(self, sound_id: str, volume: float, duration: float = 1.0) -> None:
        if not isinstance(volume, (int, float)) or not 0 <= volume <= 1:
            raise ValueError("volume debe estar entre 0.0 y 1.0.")
        if (
            not isinstance(duration, (int, float))
            or not math.isfinite(duration)
            or duration < 0
        ):
            raise ValueError("duration debe ser un número no negativo.")
        self.trigger(
            "audio.fade",
            {"id": sound_id, "volume": float(volume), "duration": float(duration)},
        )

    def set_audio_listener(
        self,
        position: tuple[float, float, float],
        *,
        forward: tuple[float, float, float] = (0, 0, -1),
        up: tuple[float, float, float] = (0, 1, 0),
    ) -> None:
        for vector in (position, forward, up):
            if len(vector) != 3 or any(
                not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in vector
            ):
                raise ValueError("Los vectores de audio deben tener tres coordenadas numéricas.")
        self.trigger(
            "audio.listener",
            {
                "position": list(position),
                "forward": list(forward),
                "up": list(up),
            },
        )

    def set_master_audio(self, volume: float) -> None:
        if (
            not isinstance(volume, (int, float))
            or not math.isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise ValueError("volume debe estar entre 0.0 y 1.0.")
        self.trigger("audio.master-volume", {"volume": float(volume)})

    def set_audio_bus_volume(self, bus: str, volume: float) -> None:
        if (
            not isinstance(volume, (int, float))
            or not math.isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise ValueError("volume debe estar entre 0.0 y 1.0.")
        self.trigger(
            "audio.bus-volume",
            {"bus": bus, "volume": float(volume)},
        )

    def set_audio_rate(self, sound_id: str, playback_rate: float) -> None:
        if (
            not isinstance(playback_rate, (int, float))
            or not math.isfinite(playback_rate)
            or not 0.25 <= playback_rate <= 4
        ):
            raise ValueError("playback_rate debe estar entre 0.25 y 4.")
        self.trigger(
            "audio.rate",
            {"id": sound_id, "playbackRate": float(playback_rate)},
        )

    def set_audio_filter(
        self,
        sound_id: str,
        index: int,
        parameter: str,
        value: float,
    ) -> None:
        if index < 0 or parameter not in {"frequency", "Q", "gain"}:
            raise ValueError("El filtro requiere un índice válido y frequency, Q o gain.")
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("El valor del filtro debe ser numérico.")
        self.trigger(
            "audio.filter",
            {
                "id": sound_id,
                "index": index,
                "parameter": parameter,
                "value": float(value),
            },
        )

    def stop_all_audio(self, bus: str | None = None) -> None:
        self.trigger("audio.stop-all", {"bus": bus})

    def fail_system(self, system_id: str, details: dict[str, Any] | None = None) -> None:
        self.trigger(
            "system.failure",
            {"id": system_id, **(details or {})},
        )

    def start_minigame(self, minigame_id: str, data: dict[str, Any] | None = None) -> None:
        self.trigger("minigame.start", {"id": minigame_id, **(data or {})})

    def apply_skin(self, skin_id: str, target: str | None = None) -> None:
        self.trigger("skin.apply", {"id": skin_id, "target": target})

    def notify(self, message: str) -> None:
        self._manager.publish("mod:notice", {"mod": self.mod_id, "text": str(message)})

    def add_overlay(self, overlay_id: str, title: str, text: str) -> None:
        if not _IDENTIFIER.fullmatch(overlay_id):
            raise ValueError(f"Identificador de panel inválido: {overlay_id!r}")
        self._manager.publish(
            "mod:overlay:add",
            {
                "id": f"{self.mod_id}:{overlay_id}",
                "title": str(title),
                "text": str(text),
            },
        )

    def remove_overlay(self, overlay_id: str) -> None:
        if not _IDENTIFIER.fullmatch(overlay_id):
            raise ValueError(f"Identificador de panel inválido: {overlay_id!r}")
        self._manager.publish(
            "mod:overlay:remove",
            {"id": f"{self.mod_id}:{overlay_id}"},
        )


class ModManager:
    def __init__(
        self,
        mods_dir: Path,
        save_store: SaveStore,
        logger: Callable[[str], None] = print,
        browser_publish: Callable[[str, Any], None] | None = None,
    ) -> None:
        self.mods_dir = mods_dir.resolve()
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.save_store = save_store
        self.log = logger
        self.browser_publish = browser_publish or (lambda _event, _payload: None)
        self.mods: dict[str, dict[str, Any]] = {}
        self.manifests: dict[str, dict[str, Any]] = {}
        self.errors: list[str] = []
        self.commands: dict[str, tuple[str, Callable[..., Any]]] = {}
        self.events: dict[str, list[tuple[str, Callable[[Any], Any]]]] = {}
        self.content: dict[str, dict[str, dict[str, Any]]] = {
            "animatronics": {},
            "systems": {},
            "modes": {},
            "minigames": {},
            "skins": {},
            "effects": {},
        }
        self._modules: list[ModuleType] = []
        self.reload()

    def reload(self) -> None:
        for mod_id in self.mods:
            self.publish("mod:remove", {"mod_id": mod_id})
        self.mods.clear()
        self.manifests.clear()
        self.errors.clear()
        self.commands.clear()
        self.events.clear()
        for definitions in self.content.values():
            definitions.clear()
        for module in self._modules:
            sys.modules.pop(module.__name__, None)
        self._modules.clear()

        for folder in sorted(self.mods_dir.iterdir(), key=lambda path: path.name.casefold()):
            if not folder.is_dir():
                continue
            manifest_path = folder / "mod.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self._validate_manifest(folder, manifest)
                mod_id = manifest["id"]
                if mod_id in self.mods:
                    raise ValueError(f"El identificador {mod_id!r} está duplicado.")
                self.manifests[mod_id] = manifest
                self.mods[mod_id] = {
                    "id": mod_id,
                    "name": manifest["name"],
                    "version": manifest["version"],
                    "enabled": manifest.get("enabled", True),
                    "status": "deshabilitado" if not manifest.get("enabled", True) else "cargado",
                }
                if not manifest.get("enabled", True):
                    continue
                api = ModAPI(self, mod_id)
                try:
                    for category, definitions in manifest.get("content", {}).items():
                        for definition in definitions:
                            self.register_content(mod_id, category, definition)
                    entrypoint = manifest.get("entrypoint")
                    if entrypoint:
                        self._load_python(folder / entrypoint, mod_id, api)
                    client_entrypoint = manifest.get("client_entrypoint")
                    if client_entrypoint:
                        self._register_client_entrypoint(mod_id, folder, client_entrypoint)
                    self._load_overlays(manifest, api)
                except Exception:
                    self._remove_mod_registrations(mod_id)
                    raise
            except (OSError, ValueError, json.JSONDecodeError, TypeError) as error:
                if folder.name in self.mods:
                    self.mods[folder.name]["status"] = "error"
                self._record_error(f"{folder.name}: {error}")
            except Exception as error:
                if folder.name in self.mods:
                    self.mods[folder.name]["status"] = "error"
                self._record_error(f"{folder.name}: error al iniciar el mod: {error}")
        self.publish("content:updated", self.get_content())

    def execute_command(self, command_line: str) -> str:
        try:
            parts = shlex.split(command_line)
        except ValueError as error:
            return f"Error: {error}"
        if not parts:
            return ""

        command, *args = parts
        if command == "help":
            builtins = (
                "help, mods, features, custom-night, skip.no [noche], night.progress, "
                "save, api, reload-mods, clear"
            )
            custom = ", ".join(sorted(self.commands)) or "(ninguno)"
            return f"Comandos: {builtins}\nMods: {custom}"
        if command == "mods":
            if not self.mods and not self.errors:
                return "No hay mods instalados en ./mods/."
            lines = [
                f"{item['id']} v{item['version']} - {item['status']}"
                for item in self.mods.values()
            ]
            lines.extend(f"ERROR: {error}" for error in self.errors)
            return "\n".join(lines)
        if command == "save":
            return f"Guardados de mods: {self.save_store.root.parent}"
        if command == "api":
            return (
                "API Python: register_command, on, emit, log, get_data, set_data, "
                "get_setting, set_setting, asset_url, notify, add_overlay, remove_overlay, "
                "register_animatronic, register_phantom, register_system, register_game_mode, "
                "register_minigame, register_skin, register_effect, trigger, set_camera_effect, "
                "add_map_marker, remove_map_marker, trigger_jumpscare, play_audio, stop_audio, "
                "pause_audio, resume_audio, set_audio_position, set_audio_volume, fade_audio, "
                "set_audio_orientation, "
                "set_audio_listener, set_master_audio, set_audio_bus_volume, set_audio_rate, "
                "set_audio_filter, stop_all_audio, fail_system, start_minigame, apply_skin."
            )
        if command == "features":
            return "\n".join(
                f"{category}: {len(definitions)}"
                for category, definitions in self.content.items()
            )
        if command == "skip.no":
            if len(args) > 1:
                return "Uso: skip.no [número de noche]"
            progress = self.save_store.get(
                "launcher", "night_progress", {"currentNight": 1, "passedNights": []}
            )
            if not isinstance(progress, dict):
                return "Error: el progreso de noches guardado no es válido."
            current_night = progress.get("currentNight", 1)
            passed_nights = progress.get("passedNights", [])
            if (
                not isinstance(current_night, int)
                or isinstance(current_night, bool)
                or current_night < 1
                or not isinstance(passed_nights, list)
                or any(
                    not isinstance(item, int) or isinstance(item, bool) or item < 1
                    for item in passed_nights
                )
            ):
                return "Error: el progreso de noches guardado no es válido."
            if args:
                try:
                    night = int(args[0])
                except ValueError:
                    return "El número de noche debe ser un entero positivo."
                if night < 1:
                    return "El número de noche debe ser un entero positivo."
            else:
                night = current_night
            if night not in passed_nights:
                passed_nights.append(night)
            progress["passedNights"] = sorted(set(passed_nights))
            progress["currentNight"] = max(
                current_night,
                night + 1,
            )
            progress["lastSkippedNight"] = night
            self.save_store.set("launcher", "night_progress", progress)
            payload = {
                "night": night,
                "nextNight": progress["currentNight"],
                "passedNights": progress["passedNights"],
                "skipped": True,
            }
            self.publish("game:command", {"name": "night.skip", "payload": payload})
            self.emit_event("night.skip", payload)
            self.emit_event("night.completed", payload)
            return (
                f"Noche {night} marcada como superada en el perfil de mods. "
                f"Siguiente: noche {progress['currentNight']}. "
                "El progreso interno del juego no se modifica."
            )
        if command == "night.progress":
            progress = self.save_store.get(
                "launcher", "night_progress", {"currentNight": 1, "passedNights": []}
            )
            return json.dumps(progress, ensure_ascii=False)
        if command == "custom-night":
            self.publish("ui:custom-night", {})
            return "Abriendo Custom Night."
        if command == "reload-mods":
            self.reload()
            return f"Mods recargados: {len(self.mods)}; errores: {len(self.errors)}."
        if command == "clear":
            return "__clear__"

        registered = self.commands.get(command)
        if registered is None:
            return f"Comando desconocido: {command}. Usa help."
        mod_id, callback = registered
        try:
            result = callback(*args)
        except Exception as error:
            message = f"[mod:{mod_id}] El comando {command} falló: {error}"
            self._record_error(message)
            return f"Error: {error}"
        return "OK" if result is None else str(result)

    def register_command(
        self,
        mod_id: str,
        name: str,
        callback: Callable[..., Any],
    ) -> None:
        if not _IDENTIFIER.fullmatch(name) or not callable(callback):
            raise ValueError("El comando debe tener un nombre válido y una función.")
        command_name = f"{mod_id}:{name}"
        if command_name in self.commands:
            raise ValueError(f"El comando {command_name!r} ya está registrado.")
        self.commands[command_name] = (mod_id, callback)

    def register_content(
        self,
        mod_id: str,
        category: str,
        definition: dict[str, Any],
    ) -> None:
        if category not in self.content:
            raise ValueError(f"Categoría de contenido desconocida: {category!r}")
        if not isinstance(definition, dict):
            raise ValueError("Cada contenido de mod debe ser un objeto JSON.")
        content_id = definition.get("id")
        name = definition.get("name")
        if not isinstance(content_id, str) or not _IDENTIFIER.fullmatch(content_id):
            raise ValueError("Cada contenido requiere un id válido.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Cada contenido requiere un nombre.")
        qualified_id = f"{mod_id}:{content_id}"
        category_content = self.content[category]
        if qualified_id in category_content:
            raise ValueError(f"El contenido {qualified_id!r} ya está registrado.")
        try:
            record = json.loads(
                json.dumps(definition, ensure_ascii=False, allow_nan=False)
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"El contenido debe ser JSON válido: {error}") from error
        record["id"] = qualified_id
        record["mod_id"] = mod_id
        self._resolve_content_assets(mod_id, record)
        category_content[qualified_id] = record

    def _register_client_entrypoint(
        self, mod_id: str, folder: Path, entrypoint: str
    ) -> None:
        if not isinstance(entrypoint, str) or not entrypoint:
            raise ValueError("client_entrypoint debe ser una ruta relativa.")
        resolved = (folder / entrypoint).resolve()
        if (
            not resolved.is_relative_to(folder.resolve())
            or not resolved.is_file()
            or resolved.suffix.lower() != ".js"
        ):
            raise ValueError(
                "client_entrypoint debe apuntar a un archivo .js dentro del mod."
            )
        self.mods[mod_id]["client_url"] = self.asset_url(mod_id, entrypoint)

    def asset_url(self, mod_id: str, relative_path: str) -> str:
        mod_root = (self.mods_dir / mod_id).resolve()
        asset = (mod_root / relative_path).resolve()
        if not asset.is_relative_to(mod_root) or not asset.is_file():
            raise ValueError("El recurso debe existir dentro de la carpeta del mod.")
        web_path = asset.relative_to(self.mods_dir).as_posix()
        return f"/mods/{web_path}"

    def _resolve_content_assets(self, mod_id: str, record: dict[str, Any]) -> None:
        for field in (
            "image",
            "sprite",
            "texture",
            "icon",
            "background",
            "jumpscare_image",
            "jumpscare_audio",
        ):
            asset = record.get(field)
            if asset is not None:
                if not isinstance(asset, str):
                    raise ValueError(f"El recurso {field!r} debe ser una ruta de texto.")
                if field == "jumpscare_audio" and Path(asset).suffix.lower() != ".mp3":
                    raise ValueError("jumpscare_audio debe ser un archivo MP3.")
                record[field] = self.asset_url(mod_id, asset)
        animations = record.get("animations")
        if animations is not None:
            if not isinstance(animations, dict):
                raise ValueError("animations debe ser un objeto con rutas de recursos.")
            for name, asset in animations.items():
                if not isinstance(asset, str):
                    raise ValueError(f"La animación {name!r} debe apuntar a un recurso.")
                animations[name] = self.asset_url(mod_id, asset)

    def trigger_game_event(
        self, mod_id: str, event_name: str, payload: Any = None
    ) -> None:
        if not _EVENT_NAME.fullmatch(event_name):
            raise ValueError(f"Nombre de evento inválido: {event_name!r}")
        event_payload = {"mod_id": mod_id, "name": event_name, "payload": payload}
        self.publish("game:command", event_payload)
        self.emit_event(event_name, payload)

    def register_event(
        self,
        mod_id: str,
        event_name: str,
        callback: Callable[[Any], Any],
    ) -> None:
        if not _EVENT_NAME.fullmatch(event_name) or not callable(callback):
            raise ValueError("El evento debe tener un nombre válido y una función.")
        self.events.setdefault(event_name, []).append((mod_id, callback))

    def emit_event(self, event_name: str, payload: Any) -> None:
        if not _EVENT_NAME.fullmatch(event_name):
            raise ValueError(f"Nombre de evento inválido: {event_name!r}")
        for mod_id, callback in self.events.get(event_name, []):
            try:
                callback(payload)
            except Exception as error:
                self._record_error(f"[mod:{mod_id}] Error en evento {event_name}: {error}")

    def emit_from_mod(self, event_name: str, payload: Any) -> None:
        self.emit_event(event_name, payload)
        self.publish(event_name, payload)

    def get_content(self) -> dict[str, list[dict[str, Any]]]:
        return {
            category: list(definitions.values())
            for category, definitions in self.content.items()
        }

    def publish(self, event_name: str, payload: Any) -> None:
        try:
            json.dumps(payload, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError(f"El evento {event_name!r} debe contener datos JSON válidos.") from error
        self.browser_publish(event_name, payload)

    def _load_python(self, entrypoint: Path, mod_id: str, api: ModAPI) -> None:
        module_name = f"fnaf3_mod_{mod_id}_{id(self)}"
        spec = importlib.util.spec_from_file_location(module_name, entrypoint)
        if spec is None or spec.loader is None:
            raise ValueError(f"No se pudo cargar el punto de entrada {entrypoint.name}.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            initialize = getattr(module, "initialize", None)
            if not callable(initialize):
                raise ValueError("main.py debe definir initialize(api).")
            initialize(api)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        self._modules.append(module)

    def _load_overlays(self, manifest: dict[str, Any], api: ModAPI) -> None:
        overlays = manifest.get("overlays", [])
        if not isinstance(overlays, list):
            raise ValueError("overlays debe ser una lista.")
        for overlay in overlays:
            if not isinstance(overlay, dict):
                raise ValueError("Cada elemento de overlays debe ser un objeto JSON.")
            api.add_overlay(
                str(overlay.get("id", "")),
                str(overlay.get("title", manifest["name"])),
                str(overlay.get("text", "")),
            )

    def _validate_manifest(self, folder: Path, manifest: Any) -> None:
        if not isinstance(manifest, dict):
            raise ValueError("mod.json debe contener un objeto JSON.")
        for field in ("id", "name", "version"):
            if not isinstance(manifest.get(field), str) or not manifest[field].strip():
                raise ValueError(f"mod.json requiere el campo de texto {field!r}.")
        if not _IDENTIFIER.fullmatch(manifest["id"]):
            raise ValueError("id solo puede usar minúsculas, números, guion y guion bajo.")
        if manifest["id"] != folder.name:
            raise ValueError("el id del mod debe coincidir con el nombre de su carpeta.")
        if not isinstance(manifest.get("enabled", True), bool):
            raise ValueError("enabled debe ser true o false.")
        if not isinstance(manifest.get("settings", {}), dict):
            raise ValueError("settings debe ser un objeto JSON.")
        content = manifest.get("content", {})
        if not isinstance(content, dict):
            raise ValueError("content debe ser un objeto JSON.")
        for category, definitions in content.items():
            if category not in self.content:
                raise ValueError(f"Categoría de contenido desconocida: {category!r}")
            if not isinstance(definitions, list):
                raise ValueError(f"content.{category} debe ser una lista.")
            if any(not isinstance(definition, dict) for definition in definitions):
                raise ValueError(
                    f"Cada elemento de content.{category} debe ser un objeto."
                )
        overlays = manifest.get("overlays", [])
        if not isinstance(overlays, list):
            raise ValueError("overlays debe ser una lista.")
        for overlay in overlays:
            if not isinstance(overlay, dict):
                raise ValueError("Cada elemento de overlays debe ser un objeto JSON.")
            if not isinstance(overlay.get("id"), str) or not _IDENTIFIER.fullmatch(
                overlay["id"]
            ):
                raise ValueError("Cada overlay requiere un id válido.")
            for field in ("title", "text"):
                if field in overlay and not isinstance(overlay[field], str):
                    raise ValueError(f"El campo {field!r} de un overlay debe ser texto.")
        entrypoint = manifest.get("entrypoint")
        if entrypoint is not None:
            if not isinstance(entrypoint, str) or not entrypoint:
                raise ValueError("entrypoint debe ser una ruta relativa.")
            resolved_entrypoint = (folder / entrypoint).resolve()
            if not resolved_entrypoint.is_relative_to(folder.resolve()):
                raise ValueError("entrypoint debe permanecer dentro de la carpeta del mod.")
            if not resolved_entrypoint.is_file() or resolved_entrypoint.suffix != ".py":
                raise ValueError("entrypoint debe apuntar a un archivo .py existente.")
        client_entrypoint = manifest.get("client_entrypoint")
        if client_entrypoint is not None:
            if not isinstance(client_entrypoint, str) or not client_entrypoint:
                raise ValueError("client_entrypoint debe ser una ruta relativa.")
            resolved_client_entrypoint = (folder / client_entrypoint).resolve()
            if not resolved_client_entrypoint.is_relative_to(folder.resolve()):
                raise ValueError(
                    "client_entrypoint debe permanecer dentro de la carpeta del mod."
                )
            if (
                not resolved_client_entrypoint.is_file()
                or resolved_client_entrypoint.suffix.lower() != ".js"
            ):
                raise ValueError(
                    "client_entrypoint debe apuntar a un archivo .js existente."
                )

    def _remove_mod_registrations(self, mod_id: str) -> None:
        self.commands = {
            command: entry
            for command, entry in self.commands.items()
            if entry[0] != mod_id
        }
        for event_name in list(self.events):
            self.events[event_name] = [
                entry for entry in self.events[event_name] if entry[0] != mod_id
            ]
            if not self.events[event_name]:
                del self.events[event_name]
        for definitions in self.content.values():
            removed = [
                content_id
                for content_id, definition in definitions.items()
                if definition["mod_id"] == mod_id
            ]
            for content_id in removed:
                del definitions[content_id]
        self.publish("mod:remove", {"mod_id": mod_id})

    def _record_error(self, message: str) -> None:
        self.errors.append(message)
        self.log(f"Error de mods: {message}")
