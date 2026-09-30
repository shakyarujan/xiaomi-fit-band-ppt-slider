# Band Slider — change PowerPoint slides from a Mi Band 10

```
Mi Band 10  --(music controls: Next / Prev)-->  Android phone (Chrome: /band page)
            --(Wi-Fi HTTP request)-->  Laptop (band_slider.py)  --> Right / Left arrow key --> PowerPoint
```

The band can't connect to Windows directly (it uses Xiaomi's encrypted Bluetooth
protocol and only talks to the Mi Fitness app), so the phone relays the button presses.

**Why a Chrome page and not MacroDroid?** The band's music buttons don't send media-button
key events. Mi Fitness sends Next / Previous to whichever app is *playing audio* (the active
media session). MacroDroid's "Media Button Pressed" trigger never sees them. The `/band` page
plays inaudible audio so Chrome becomes that player, and it forwards Next / Previous to the laptop.

## Requirements
- Windows laptop with Python 3.8+ and Microsoft PowerPoint
- Android phone with Chrome and Mi Fitness, on the same Wi-Fi as the laptop
- No extra Python packages: standard library only (see `requirements.txt`)

## 1. Laptop
1. Run:
   ```
   python band_slider.py            # optional: --port 8765
   ```
   It prints your URLs, e.g. `http://192.168.1.20:8765/band`.
2. The first time, Windows Firewall asks for permission. Allow **Private networks**.
3. Test it: open `http://<laptop-ip>:8765/` in the phone's browser and tap the buttons.

| URL | What it does |
|---|---|
| `http://<laptop-ip>:8765/next` | Next slide (Right arrow) |
| `http://<laptop-ip>:8765/prev` | Previous slide (Left arrow) |
| `http://<laptop-ip>:8765/` | Big-button remote page (backup / iPhone) |
| `http://<laptop-ip>:8765/band` | Mi Band page: open in phone Chrome |

Before pressing the key, the script brings the PowerPoint window to the front, so it works
even when another window (like a browser) is focused.

## 2. Phone (one-time setup)
1. **Mi Fitness:** turn on music control for the band, and allow Mi Fitness under
   *Settings → Apps → Special app access → Notification access*.
2. **Chrome flag:** Chrome only gives media controls to `https` pages, so allow this `http` page once:
   - Open `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
   - Enter `http://<laptop-ip>:8765` (your real IP), set it to **Enabled**, and tap **Relaunch**.

## 3. Present
1. Start `band_slider.py` on the laptop.
2. On the phone, close other music apps, open `http://<laptop-ip>:8765/band` in Chrome and tap
   **Start band control** (the button turns green). Keep the tab open; you can lock the phone.
3. In PowerPoint, press **F5** to start the slideshow.
4. Open the music screen on the band and press ▶▶ / ◀◀ to change slides.

## Troubleshooting
| Problem | Fix |
|---|---|
| URL works on the laptop but not from the phone | Use the IP the script prints (not `localhost`), same Wi-Fi, allow Python on **Private** in Windows Firewall |
| Key is sent but the slide doesn't move | Click **Enable Editing** if the file is in Protected View; if PowerPoint runs as administrator, run the script as administrator too |
| Red "media controls are blocked" message on `/band` | The Chrome flag isn't set for the exact `http://<ip>:<port>`; set it and relaunch Chrome |
| Mi Fitness / band shows "Not playing" | Check that a **Band Slider** media card appears in the notification shade. If it does, give Mi Fitness notification access; if not, reopen `/band` and tap Start |
| Laptop IP changed | Update the Chrome flag and the URL you open on the phone |

## Notes
- Presses less than 0.35 s apart are ignored, so an accidental double tap only moves one slide.
- **iPhone:** the `/band` page isn't supported. Use the `/` remote page in Safari instead.
- MacroDroid / Tasker can still call `/next` and `/prev` (e.g. from a widget or shortcut), but not from the band's music buttons.
