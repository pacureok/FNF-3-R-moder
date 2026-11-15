# FNAF3 WINT MODS remix

Iniciador de escritorio para Windows con PyQt6. El juego original sigue usando
su runtime HTML5 y sus recursos; el iniciador los carga en una ventana nativa
mediante un servidor local enlazado únicamente a `127.0.0.1`. La ventana activa
la rasterización y Canvas 2D acelerados por GPU cuando está disponible. El
juego se maximiza y escala al área completa de la ventana al redimensionarla.
Los archivos `.cch` y `.cc1`, además de los 64 MP3, se precargan antes de iniciar el
runtime y se muestra el progreso. El runtime queda configurado para seleccionar
MP3 como único formato de audio.
Se conservaron `resources/0013.ogg` y `resources/0013.wav` porque tenían
cambios locales; el runtime no los selecciona.
Al iniciar el juego aparece el botón **Créditos**. El panel atribuye el motor,
el mod y su launcher a Pacure, y reproduce la pista de créditos incluida.
Los MP3 `0031` y `0033`–`0037` siguen el eje X del mouse sobre el lienzo:
X positiva panea a la izquierda; X negativa se centra en mono. El eje Y no
afecta el paneo.
Se sirven los PNG originales, sin sustituirlos por variantes `_HD`. El iniciador
también publica la actividad de Discord como **Jugando** usando el ID de
aplicación `1568717580913483957`; Discord de escritorio debe estar abierto.

## Iniciar

Se requiere Python 3.10 o posterior.

```powershell
py -m pip install -r requirements.txt
py main.py
```

También se puede iniciar desde la carpeta del proyecto con:

```powershell
py .\main.py
```

## Guardados, consola y mods

Los guardados nativos del runtime HTML5 usan `localStorage`. El launcher mantiene
una dirección local estable y un perfil persistente para que esos datos sobrevivan
al cierre del juego. Los datos escritos por mods se guardan aparte en
`saves\mods\<id>.json`; la caché del navegador también está bajo `saves\`.

Pulsa **F12** para abrir la consola de desarrollo. Comandos disponibles:

```text
help
mods
features
custom-night
skip.no [número de noche]
night.progress
save
api
reload-mods
clear
example:hello
example:panel
example:hide
example:spawn
example:failure
```

`skip.no` marca la noche indicada (o la siguiente del perfil de mods) como
superada y guarda el progreso en `saves\mods\launcher.json`. También emite los
eventos `night.skip` y `night.completed` para mods. El runtime original no ofrece
un gancho documentado para cambiar su progreso interno, por lo que este comando
no modifica la partida nativa de Clickteam. `night.progress` muestra el avance
guardado por el launcher. Pulsa **F11** para ocultar o restaurar la interfaz
añadida por el launcher y los mods; el juego continúa visible y ejecutándose.

El botón **Custom Night** abre los controles de agresividad y modificadores.
**Contenido de mods** muestra las definiciones registradas y permite emitir
eventos de prueba para animatrónicos, sistemas, modos, minijuegos, skins y efectos.
Esas acciones pasan a los mods activos; las acciones de cámara y los marcadores
tienen una representación visual superpuesta.

Los mods se colocan en `mods\<id>\`. Cada carpeta contiene un `mod.json` y puede
incluir un `main.py` con `initialize(api)` y un `client.js` indicado en el campo
opcional `client_entrypoint`. El mod `example` sirve como ejemplo funcional.
Los manifiestos aceptan `id`, `name`, `version`, `enabled`, `entrypoint`,
`client_entrypoint`, `settings`, `content` y `overlays`.

La API Python incluye:

- `register_command(name, callback)` para agregar comandos F12 con prefijo del mod.
- `on(event, callback)` y `emit(event, payload)` para eventos entre mods y la página.
- `register_animatronic`, `register_phantom`, `register_system`, `register_game_mode`,
  `register_minigame`, `register_skin` y `register_effect` para registrar contenido.
- `get_data` / `set_data` y `get_setting` / `set_setting` para datos persistentes.
- `asset_url(path)` para obtener la URL de un recurso dentro del mod.
- `trigger`, `set_camera_effect`, `add_map_marker`, `trigger_jumpscare`, `fail_system`,
  `start_minigame`, `apply_skin`, `play_audio` y `stop_audio` para solicitar acciones del juego.
- Audio adicional: `pause_audio`, `resume_audio`, `stop_all_audio`, `set_audio_listener`,
  `set_audio_position`, `set_audio_orientation`, `set_audio_volume`, `fade_audio`,
  `set_audio_bus_volume`, `set_audio_rate` y `set_audio_filter`.
- `notify`, `add_overlay` y `remove_overlay` para notificaciones y paneles superpuestos.
- `log` para escribir mensajes de diagnóstico.

Ejemplo de audio espacial desde un mod Python:

```python
api.set_audio_listener((0, 0, 0))
api.play_audio(
    "sounds/vent.mp3",
    sound_id="vent",
    position=(4, 0, -2),
    volume=0.8,
    loop=True,
    options={
        "bus": "ambience",
        "panningModel": "HRTF",
        "distanceModel": "inverse",
        "refDistance": 1,
        "maxDistance": 30,
        "rolloffFactor": 1.5,
        "filters": [{"type": "lowpass", "frequency": 5000}],
    },
)
api.set_audio_position("vent", (2, 0, -1))
api.fade_audio("vent", 0.2, duration=2)
```

En JavaScript, `window.FNAF3.api.play3DAudio(id, src, [x, y, z], options)` crea
una fuente espacial HRTF. `playAudio(options)` permite elegir `bus`, filtros,
distancia y reproducción; las funciones `setAudioListener`, `setAudioPosition`,
`setAudioOrientation`, `setAudioVolume`, `fadeAudio`, `setMasterAudio`,
`setAudioBusVolume`, `setAudioRate`, `setAudioFilter`, `pauseAudio`,
`resumeAudio`, `stopAudio` y `stopAllAudio` controlan la mezcla. Los buses se
crean al usarse. Los filtros disponibles son lowpass, highpass, bandpass,
lowshelf, highshelf, peaking, notch y allpass. El audio de los mods usa un
contexto Web Audio y buses separados del audio original; acepta únicamente MP3
locales en `resources\` o en la carpeta del propio mod. Los eventos
`audio.started`, `audio.ended` y `audio.error` notifican el resultado a los mods.
El navegador puede exigir una interacción del usuario antes de reproducir audio.

Los manifiestos JSON pueden definir las mismas categorías con listas bajo
`content.animatronics`, `content.systems`, `content.modes`, `content.minigames`,
`content.skins` y `content.effects`. Las rutas de `image`, `sprite`, `texture`,
`icon`, `background`, `jumpscare_image`, `jumpscare_audio` y `animations` deben
apuntar a archivos del mod. La pantalla Custom Night incluye controles de
agresividad 0–20 para Springtrap y los animatrónicos registrados, y modificadores
de audio, apagón, luces, tiempo y Multi-Springtrap. Al iniciarla emite `night.start`;
los mods activos implementan las reacciones a ese evento.
Otros eventos que pueden escuchar/emitir los mods incluyen `animatronic.spawn`,
`animatronic.remove`, `camera.effect`, `camera.flashing`, `camera.map`,
`map.marker`, `map.marker.remove`, `system.failure`, `jumpscare`,
`minigame.start`, `mode.start` y `skin.apply`.

En JavaScript, `window.FNAF3.api` permite obtener el catálogo, suscribirse a
eventos (`on`), emitirlos (`emit`), abrir Custom Night y solicitar efectos,
marcadores, jumpscares, minijuegos o fallas. Opcionalmente, `client_entrypoint`
en `mod.json` carga un script del navegador con permisos de origen local.
`window.FNAF3Runtime.registerExtension(id, initialize)` recibe el objeto del
runtime y el canvas cuando el motor arranca; `getInstance()` también expone la
instancia para extensiones avanzadas. La instancia y los detalles internos del
motor Clickteam no tienen una API estable: manipularlos directamente puede
romperse y no equivale a añadir personajes nativos al mapa del juego. La API
proporciona un catálogo, eventos, un panel de contenido y capas visuales de mod;
cualquier lógica específica del runtime debe implementarse en la extensión.
Aunque la instancia queda disponible para hooks avanzados, registrar contenido
no lo inserta por sí mismo en los objetos o escenas originales. Sin el proyecto
fuente de Clickteam o puntos de extensión internos documentados, no hay forma
segura de prometer nuevos enemigos nativos, sistemas conectados al estado de la
noche, cambios de texturas del motor o minijuegos que alteren el progreso.
Las funciones base no modifican el binario del runtime.

Los scripts Python y JavaScript de mods se ejecutan con los permisos del usuario
y no están aislados. `reload-mods` recarga mods Python y el catálogo; para volver
a ejecutar scripts de navegador, reinicia el juego. Instala únicamente mods de
fuentes confiables.

El inspector Rust también inspecciona las carpetas de mods:

```powershell
cargo run --target x86_64-pc-windows-gnu --manifest-path .\tools\game_inspector\Cargo.toml -- inspect-mods .\mods
```

No se sustituyeron los PNG por GIF: los archivos de imagen forman parte de los
recursos del runtime y no hay secuencias de fotogramas GIF identificables en el
proyecto. Convertirlos sin el proyecto fuente podría impedir que el juego cargue.

## Inspeccionar los archivos del runtime con Rust

Desde la carpeta del proyecto, ejecuta el inspector de solo lectura:

```powershell
cargo run --target x86_64-pc-windows-gnu --manifest-path .\tools\game_inspector\Cargo.toml
```

Muestra las entradas ZIP de `fnaf 3.cc1` y los bytes iniciales de `fnaf 3.cch`;
no modifica ninguno de los dos archivos. También acepta rutas explícitas como
argumentos.
