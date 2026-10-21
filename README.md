# Karty lojalnościowe dla Home Assistant

Wszystkie karty sklepowe (Biedronka, Lidl, Rossmann…) w jednym widoku Home Assistanta.
Pokazuje kod kreskowy albo QR do zeskanowania przy kasie, a karty z kodem zmieniającym się co chwilę
(np. Żappka, Lidl Plus) otwierają aplikację sklepu. Sam dobiera logo sklepu,
a karty widzą i dodają wszyscy domownicy.

---

## Instalacja krok po kroku

Całość zajmie ok. 10 minut. Niczego nie trzeba programować — tylko kopiować i wklejać.

### Krok 1. Zainstaluj button-card

Potrzebny jest **HACS** ([jak zainstalować HACS](https://hacs.xyz/docs/use/)).

1. Otwórz **HACS** w menu po lewej.
2. Wpisz w wyszukiwarkę **button-card**.
3. Kliknij go → **Pobierz** → **Pobierz**.

### Krok 2. Skopiuj pliki

Potrzebny jest dodatek **Terminal & SSH**:
**Ustawienia → Dodatki → Sklep z dodatkami → Terminal & SSH → Zainstaluj → Uruchom → Otwórz interfejs**.

W czarnym oknie wklej **całość** poniżej i naciśnij Enter:

```bash
cd /tmp && rm -rf karty && git clone https://github.com/chocolatescode/ha-loyality-cards karty \
&& mkdir -p /config/custom_components /config/www \
&& cp -r karty/custom_components/karty /config/custom_components/ \
&& cp -r karty/karty /config/ \
&& cp -r karty/www/karty /config/www/ \
&& rm -rf karty && echo "GOTOWE"
```

Na końcu ma się pojawić napis **GOTOWE**.

### Krok 3. Dopisz jedną rzecz do configuration.yaml

Otwórz plik `configuration.yaml` (np. dodatkiem **File editor** albo **Studio Code Server**).

**Jeśli w pliku NIE MA linijki `homeassistant:`** — dopisz na samym końcu:

```yaml
homeassistant:
  packages:
    karty: !include karty/package.yaml
```

**Jeśli linijka `homeassistant:` JUŻ JEST** — dopisz pod nią tylko brakujące linie
(odstępy muszą być spacjami, dokładnie jak niżej):

```yaml
homeassistant:
  packages:                               # <- tę dopisz, jeśli jej nie ma
    karty: !include karty/package.yaml    # <- tę dopisz zawsze
```

Zapisz plik.

### Krok 4. Uruchom ponownie Home Assistanta

**Ustawienia → System → ikona zasilania (prawy górny róg) → Uruchom ponownie Home Assistant**.

### Krok 5. Dodaj widok „Karty”

1. Otwórz plik [dashboard/karty-view.yaml](dashboard/karty-view.yaml) → kliknij **Copy raw file**
   (ikona dwóch kwadracików nad treścią pliku).
2. W Home Assistancie otwórz swój dashboard → **ołówek** (prawy górny róg) → **+** obok zakładek widoków.
3. W okienku nowego widoku kliknij **⋮** (prawy górny róg) → **Edytuj w YAML**.
4. Zaznacz wszystko, co tam jest, usuń i **wklej** skopiowany tekst.
5. **Zapisz** → **Gotowe**.

Gotowe! Na pasku pojawi się zakładka z ikoną karty.

---

## Jak używać

- **Dodanie karty** — przycisk dodawania w widoku; wpisz nazwę sklepu i numer karty.
  Logo pojawi się samo po chwili.
- **Przy kasie** — stuknij kartę, pokaże się duży kod do zeskanowania.

## Gdy coś nie działa

| Objaw | Co zrobić |
|---|---|
| Zamiast widoku czerwony błąd „custom:button-card” | Nie zainstalowano button-card (krok 1) albo trzeba odświeżyć stronę (Ctrl+F5) |
| Karty się nie zapisują | Sprawdź krok 3 i zrestartuj HA |
| Brak logo sklepu | Logo pobierane jest do godziny; nie każdy sklep je ma — wtedy zostaje sama nazwa |

## Opcjonalnie: jaśniejszy ekran przy kasie

Widok może rozjaśniać ekran telefonu z aplikacją Home Assistant, gdy pokazuje kod.
W `karty-view.yaml` znajdź `const DEV = {};` i wpisz swoje telefony, np.:

```js
const DEV = { 'SM-A576B': 'mobile_app_moj_telefon' };
```

(model telefonu → nazwa usługi `notify` z aplikacji HA).

## Co jest w środku

| Ścieżka | Opis |
|---|---|
| `custom_components/karty/` | Integracja: wspólny magazyn kart (`.storage/karty`) dla wszystkich użytkowników, także bez uprawnień admina |
| `karty/logo.py` | Skrypt pobierający logo sklepów (Wikidata → strona sklepu → ikona) |
| `karty/package.yaml` | Sensor „Karty loga” + włączenie integracji |
| `www/karty/` | Biblioteki JsBarcode i qrcode.js (MIT) oraz lista sklep → strona www |
| `dashboard/karty-view.yaml` | Widok „Karty” |
