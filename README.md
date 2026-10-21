# Karty lojalnościowe dla Home Assistant

Widok dashboardu z kartami lojalnościowymi (kody kreskowe / QR, TOTP, skróty do aplikacji sklepów)
ze wspólnym magazynem kart dla wszystkich domowników — również użytkowników bez uprawnień admina.

## Zawartość

| Ścieżka | Opis |
|---|---|
| `custom_components/karty/` | Integracja: magazyn kart w `.storage/karty`, komendy websocket `karty/get` i `karty/set` dla każdego zalogowanego użytkownika |
| `karty/logo.py` | Skrypt pobierający logo sklepów (Wikidata → strona sklepu → ikona) do `www/karty/logos/` |
| `karty/package.yaml` | Pakiet HA: sensor `command_line` „Karty loga” + włączenie integracji `karty:` |
| `www/karty/` | Biblioteki JsBarcode i qrcode.js (MIT) oraz mapa sklep → domena (`sklepy.json`) |
| `dashboard/karty-view.yaml` | Widok „Karty” (panel z `custom:button-card`) |

## Instalacja

1. Skopiuj `custom_components/karty`, `karty/` i `www/karty/` do katalogu konfiguracji HA.
2. Dołącz pakiet w `configuration.yaml`:
   ```yaml
   homeassistant:
     packages:
       karty: !include karty/package.yaml
   ```
3. Zainstaluj z HACS [button-card](https://github.com/custom-cards/button-card).
4. Zrestartuj Home Assistant.
5. Dodaj widok z `dashboard/karty-view.yaml` w edytorze YAML dashboardu.
