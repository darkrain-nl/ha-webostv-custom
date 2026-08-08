# LG webOS TV Custom Screen Control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A custom integration override for Home Assistant that adds native **Screen Power Switch** control (`switch.<tv_name>_screen`) to LG webOS TVs.

---

## 🌟 Features

- **Native Screen Switch Entity**: Provides a dedicated switch (`switch.<tv_name>_screen`) in Home Assistant to turn the TV display on or off while keeping TV audio and background system running.
- **Real-Time State Tracking**: Listens directly to WebSocket power state notifications from the TV (`is_screen_on`) without requiring external polling automations.
- **Native WebOS Commands**: Executes `com.webos.service.tvpower/power/turnOffScreen` and `turnOnScreen`.
- **Modern Turn On Trigger**: `webostv.turn_on_requested` is a first-class UI trigger — it shows up in the automation editor as *"TV is requested to turn on"* with a target selector, so it can be targeted by entity, device, area, floor or label instead of YAML-only editing. The original `webostv.turn_on` trigger keeps working alongside it.

---

## 📦 Installation via HACS

1. Open **Home Assistant** -> **HACS**.
2. Click the **3 dots** (top right) -> **Custom repositories**.
3. Add Repository URL:
   ```text
   https://github.com/darkrain-nl/ha-webostv-custom
   ```
4. Category: **Integration** -> Click **Add**.
5. Find **LG webOS TV Custom Screen Control**, click **Download**, and select the latest release (`v1.0.19`).
6. **Restart Home Assistant**.

---

## 🚀 Usage

Once Home Assistant has restarted, your LG webOS TV device will automatically show a new switch entity named `switch.<tv_name>_screen`.

### Automation Example

```yaml
alias: Turn off TV screen when listening to music
trigger:
  - platform: state
    entity_id: media_player.lg_webos_tv
    to: "playing"
action:
  - action: switch.turn_off
    target:
      entity_id: switch.lg_webos_tv_screen
```

### Turn On Trigger

Fires when Home Assistant is asked to turn the TV on (for example by
`media_player.turn_on`), so the automation can do the actual waking — Wake on LAN,
a smart plug, an IR blaster.

```yaml
triggers:
  - trigger: webostv.turn_on_requested
    target:
      entity_id: media_player.lg_webos_tv
actions:
  - action: wake_on_lan.send_magic_packet
    data:
      mac: aa:bb:cc:dd:ee:ff
```

`target` also accepts `device_id`, `area_id`, `floor_id` and `label_id`.

The older `webostv.turn_on` trigger, which takes a top-level `entity_id` or `device_id`,
keeps working indefinitely — it is not deprecated. It stays out of the automation
editor's trigger list, so the editor never renders or rewrites a stored config that
uses it, the same way `sun` and `calendar` handle their legacy triggers.

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
