"""Wspólny magazyn kart lojalnościowych.

Frontend system_data pozwala zapisywać tylko adminom, a karty mają móc dodawać
wszyscy domownicy (również Dziadek, który nie jest adminem). Ta integracja
trzyma karty w .storage/karty i udostępnia komendy websocket karty/get
i karty/set dla każdego zalogowanego użytkownika.
"""

from __future__ import annotations

import glob
import json
import logging
import os
from typing import Any

try:
    import probatio as vol
except ImportError:  # starsze wersje HA
    import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

DOMAIN = "karty"
KEY = "karty_lojalnosciowe"


def _old_cards(config_dir: str) -> list[dict[str, Any]]:
    """Karty zapisane wcześniej przez panel: system_data, a gdy pusto, user_data wszystkich."""
    sysf = os.path.join(config_dir, ".storage", "frontend.system_data")
    try:
        with open(sysf, encoding="utf-8") as f:
            cards = ((json.load(f).get("data") or {}).get(KEY) or {}).get("cards") or []
        if cards:
            return cards
    except (OSError, ValueError):
        pass
    merged: list[dict[str, Any]] = []
    seen = set()
    for path in sorted(glob.glob(os.path.join(config_dir, ".storage", "frontend.user_data_*"))):
        try:
            with open(path, encoding="utf-8") as f:
                cards = ((json.load(f).get("data") or {}).get(KEY) or {}).get("cards") or []
        except (OSError, ValueError):
            continue
        for c in cards:
            sig = (c.get("name"), c.get("code"), c.get("type"))
            if sig not in seen:
                seen.add(sig)
                merged.append(c)
    return merged


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    store: Store[dict[str, Any]] = Store(hass, 1, DOMAIN)
    data = await store.async_load()
    if data is None:
        cards = await hass.async_add_executor_job(_old_cards, hass.config.config_dir)
        data = {"cards": cards}
        await store.async_save(data)
        _LOGGER.info("Karty: utworzono wspólny magazyn, przeniesiono %d kart", len(cards))
    hass.data[DOMAIN] = {"store": store, "data": data}

    websocket_api.async_register_command(hass, ws_get)
    websocket_api.async_register_command(hass, ws_set)
    return True


@websocket_api.websocket_command({vol.Required("type"): "karty/get"})
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], {"value": hass.data[DOMAIN]["data"]})


@websocket_api.websocket_command(
    {vol.Required("type"): "karty/set", vol.Required("value"): dict}
)
@websocket_api.async_response
async def ws_set(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    value = msg["value"]
    if not isinstance(value.get("cards"), list):
        connection.send_error(msg["id"], "invalid_format", "value.cards musi być listą")
        return
    d = hass.data[DOMAIN]
    d["data"] = value
    await d["store"].async_save(value)
    user = connection.user
    _LOGGER.info("Karty: %s zapisał(a) %d kart", user.name if user else "?", len(value["cards"]))
    connection.send_result(msg["id"])

