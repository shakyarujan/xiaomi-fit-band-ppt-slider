# Band Slider — change PowerPoint slides from a Mi Band 10

```
Mi Band 10  --(music controls: Next / Prev)-->  Android phone (MacroDroid)
            --(Wi-Fi HTTP request)-->  Laptop (band_slider.py)  --> Right / Left arrow key --> PowerPoint
```

The band can't connect to Windows directly (it uses Xiaomi's encrypted Bluetooth
protocol and only talks to the phone app), so the phone relays the button presses.

## 1. Laptop
1. Run `python band_slider.py`. It prints your URLs, e.g. `http://192.168.1.20:8765/next`.
2. The first time, Windows Firewall asks for permission. Allow **Private networks**.
3. Test it: open `http://<laptop-ip>:8765/` in the phone's browser and tap the buttons.

## 2. Phone (Android + MacroDroid, free)
1. In **Mi Fitness**, turn on the band's music control (Band settings → Music, or similar).
2. Install **MacroDroid** and create two macros:
   - Trigger: **Media Button Pressed → Next** (enable the option to block/consume the button)
     Action: **HTTP Request → GET** `http://<laptop-ip>:8765/next`
   - Trigger: **Media Button Pressed → Previous**
     Action: **HTTP Request → GET** `http://<laptop-ip>:8765/prev`
3. Open the music screen on the band. Pressing ▶▶ / ◀◀ should now change the slides.

Tip: don't play any music on the phone while you present, or the music app may take the button presses.

## 3. Present
Open PowerPoint, press **F5**, and keep the slideshow window in focus.

## Notes
- The phone and laptop must be on the same Wi-Fi (a phone hotspot works too).
- Presses less than 0.35 s apart are ignored, so an accidental double tap only moves one slide.
- **iPhone:** iOS won't let apps catch the band's music buttons. Use the `/` remote page in Safari instead.

### Short work flow description
Band Slider - control PowerPoint on this laptop from your Mi Band (via your phone).

The laptop runs this small web server. Anything on the same Wi-Fi can hit:
    http://<laptop-ip>:8765/next   -> next slide  (Right arrow)
    http://<laptop-ip>:8765/prev   -> previous slide (Left arrow)
    http://<laptop-ip>:8765/       -> big-button remote page (phone fallback)

Your phone (MacroDroid / Tasker) turns Mi Band music-control presses into those
requests. No extra Python packages needed - standard library only.

Run:  python band_slider.py        (optional: --port 8765)
