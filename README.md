# LG webOS TV Custom Screen Control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A custom integration override for Home Assistant that adds native **Screen Power Switch** control (`switch.<tv_name>_screen`) to LG webOS TVs.

---

## 🌟 Features

- **Native Screen Switch Entity**: Provides a dedicated switch (`switch.<tv_name>_screen`) in Home Assistant to turn the TV display on or off while keeping TV audio and background system running.
- **Real-Time State Tracking**: Listens directly to WebSocket power state notifications from the TV (`is_screen_on`) without requiring external polling automations.
- **Native WebOS Commands**: Executes `com.webos.service.tvpower/power/turnOffScreen` and `turnOnScreen`.

---

## 📦 Installation via HACS

1. Open **Home Assistant** -> **HACS**.
2. Click the **3 dots** (top right) -> **Custom repositories**.
3. Add Repository URL:
   ```text
   https://github.com/darkrain-nl/ha-webostv-custom
   ```
4. Category: **Integration** -> Click **Add**.
5. Find **LG webOS TV Custom Screen Control**, click **Download**, and select the latest release (`v1.0.2`).
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

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
