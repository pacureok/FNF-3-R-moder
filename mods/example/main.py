def initialize(api):
    api.on("runtime.ready", lambda _payload: api.log("El runtime del juego está listo."))
    api.register_command("hello", lambda: api.get_setting("greeting"))
    api.register_command(
        "panel",
        lambda: api.add_overlay(
            "example",
            "Mod de ejemplo",
            "Este panel se agregó usando la API de mods.",
        ),
    )
    api.register_command("hide", lambda: api.remove_overlay("example"))
    api.register_command(
        "spawn",
        lambda: api.trigger(
            "animatronic.spawn",
            {
                "id": "example:phantom-bonnie",
                "instance": "example:phantom-bonnie:console",
                "label": "Phantom Bonnie",
                "camera": "CAM 01",
            },
        ),
    )
    api.register_command(
        "failure",
        lambda: api.trigger(
            "system.failure",
            {"id": "example:temperature", "name": "Control de temperatura"},
        ),
    )

    def handle_custom_night(config):
        levels = config.get("animatronics", {})
        aggression = levels.get("example:phantom-bonnie", 0)
        if aggression:
            api.trigger(
                "animatronic.spawn",
                {
                    "id": "example:phantom-bonnie",
                    "instance": "example:phantom-bonnie:night",
                    "label": "Phantom Bonnie",
                    "camera": "CAM 01",
                    "aggression": aggression,
                },
            )
        if config.get("modifiers", {}).get("flashingLights"):
            api.trigger("camera.flashing", {"enabled": True})
        if config.get("modifiers", {}).get("multiSpringtrap"):
            api.trigger(
                "animatronic.spawn",
                {
                    "id": "springtrap",
                    "instance": "example:springtrap:second",
                    "label": "Springtrap II",
                    "camera": "CAM 02",
                },
            )
        api.set_setting("last_custom_night", config)

    api.on("night.start", handle_custom_night)
