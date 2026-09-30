import argparse
import ctypes
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VK_LEFT, VK_RIGHT = 0x25, 0x27
KEYEVENTF_KEYUP = 0x0002
DEBOUNCE_SECONDS = 0.35  # ignore accidental double taps from the band

VK_MENU = 0x12  # Alt
SW_RESTORE = 9

_user32 = ctypes.windll.user32
_user32.FindWindowW.restype = ctypes.c_void_p
_last_press = 0.0


def focus_powerpoint() -> str:
    """Bring the PowerPoint slideshow (or editor) window to the front.

    Key presses go to whatever window is in front, so without this the arrow
    key lands in the browser / terminal instead of PowerPoint.
    """
    # "screenClass" = running slideshow, "PPTFrameClass" = normal editor window
    for cls, name in (("screenClass", "slideshow"), ("PPTFrameClass", "editor")):
        hwnd = _user32.FindWindowW(cls, None)
        if hwnd:
            if _user32.GetForegroundWindow() != hwnd:
                if _user32.IsIconic(hwnd):
                    _user32.ShowWindow(hwnd, SW_RESTORE)
                # Windows blocks background apps from stealing focus; a tap of
                # Alt lifts that restriction for the next SetForegroundWindow.
                _user32.keybd_event(VK_MENU, 0, 0, 0)
                _user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
                _user32.SetForegroundWindow(hwnd)
                time.sleep(0.05)
            return name
    return "not found"


def press(vk: int) -> str:
    global _last_press
    now = time.monotonic()
    if now - _last_press < DEBOUNCE_SECONDS:
        return "ignored (debounce)"
    _last_press = now
    target = focus_powerpoint()
    _user32.keybd_event(vk, 0, 0, 0)
    _user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    return f"sent to PowerPoint {target}"


REMOTE_PAGE = """<!doctype html><html><head><meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>Band Slider</title><style>
                body{margin:0;height:100vh;display:flex;flex-direction:column;font-family:sans-serif;background:#111}
                button{flex:1;border:0;font-size:3rem;color:#fff;margin:6px;border-radius:16px}
                #p{background:#444}#n{background:#1f6feb}</style></head><body>
                <button id="p" onclick="fetch('/prev')">&#9664; Prev</button>
                <button id="n" onclick="fetch('/next')">Next &#9654;</button>
                </body></html>
            """

# The Mi Band's music controls don't send media-button key events; they drive the
# phone's *active media session*. This page plays silent audio in Chrome so it
# becomes that session, then turns Next/Previous into /next and /prev requests.
BAND_PAGE = """<!doctype html><html><head><meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>Band Slider</title>
                    <style>
                        body{margin:0;padding:16px;font-family:sans-serif;background:#111;color:#eee;text-align:center}
                        button{width:100%;padding:28px;font-size:1.6rem;border:0;border-radius:16px;background:#1f6feb;color:#fff}
                        #s{margin:18px 0;font-size:1.2rem}#log{font-size:.9rem;color:#aaa;text-align:left;white-space:pre-line}
                        .warn{color:#f85149}
                    </style>
                </head>
                <body>
                    <button id="go">Start band control</button>
                    <div id="s">Tap Start, then use Next / Previous on the band's music screen.</div>
                    <div id="log"></div>
                    <script>
                        const $ = id => document.getElementById(id);
                        const log = m => { $('log').textContent = new Date().toLocaleTimeString() + '  ' + m + '\\n' + $('log').textContent; };

                        if (!('mediaSession' in navigator)) {
                        $('s').innerHTML = '<span class="warn">Media controls are blocked because this page is http.<br>' +
                            'In Chrome open <b>chrome://flags/#unsafely-treat-insecure-origin-as-secure</b>, add <b>' +
                            location.origin + '</b>, enable it, relaunch Chrome.</span>';
                        $('go').disabled = true;
                        }

                        // 30 s of silent 8 kHz 8-bit mono WAV (Chrome only shows media controls for audio > 5 s)
                        function silentWav(sec) {
                        const rate = 8000, n = rate * sec, buf = new ArrayBuffer(44 + n), v = new DataView(buf);
                        const str = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
                        str(0, 'RIFF'); v.setUint32(4, 36 + n, true); str(8, 'WAVEfmt ');
                        v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
                        v.setUint32(24, rate, true); v.setUint32(28, rate, true); v.setUint16(32, 1, true);
                        v.setUint16(34, 8, true); str(36, 'data'); v.setUint32(40, n, true);
                        // Not pure digital silence: Chrome may skip creating a media session for it.
                        // +/-1 step of noise is inaudible but counts as real audio.
                        const d = new Uint8Array(buf, 44);
                        for (let i = 0; i < n; i++) d[i] = 128 + ((Math.random() * 3) | 0) - 1;
                        return URL.createObjectURL(new Blob([buf], {type: 'audio/wav'}));
                        }

                        const audio = new Audio(silentWav(30));
                        audio.loop = true;

                        async function send(cmd) {
                        try { log(cmd + ' -> ' + await (await fetch('/' + cmd)).text()); }
                        catch (e) { log(cmd + ' FAILED: ' + e); }
                        }

                        $('go').onclick = async () => {
                        const ms = navigator.mediaSession;
                        ms.metadata = new MediaMetadata({title: 'Band Slider', artist: 'PowerPoint remote'});
                        try { await audio.play(); } catch (e) { log('audio play FAILED: ' + e); return; }
                        setInterval(() => { if (audio.paused) { audio.play(); log('audio resumed'); } }, 3000);
                        ms.setActionHandler('nexttrack', () => send('next'));
                        ms.setActionHandler('previoustrack', () => send('prev'));
                        // Keep the session alive if the band's play/pause is pressed
                        ms.setActionHandler('pause', () => { audio.play(); ms.playbackState = 'playing'; });
                        ms.setActionHandler('play', () => { audio.play(); ms.playbackState = 'playing'; });
                        ms.playbackState = 'playing';
                        $('go').textContent = 'Running - keep this tab open';
                        $('go').style.background = '#238636';
                        log('ready');
                        };
                    </script>
                </body>
            </html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/").lower()
        if path in ("/next", "/n"):
            self._reply(200, "next: " + press(VK_RIGHT))
        elif path in ("/prev", "/previous", "/p"):
            self._reply(200, "prev: " + press(VK_LEFT))
        elif path == "":
            self._reply(200, REMOTE_PAGE, "text/html")
        elif path == "/band":
            self._reply(200, BAND_PAGE, "text/html")
        else:
            self._reply(404, "use /next or /prev")

    do_POST = do_GET  # some automation apps default to POST

    def _reply(self, code, body, ctype="text/plain"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {self.client_address[0]} {self.path}")


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no packet is sent; just picks the Wi-Fi interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    port = ap.parse_args().port
    ip = lan_ip()
    print("Band Slider running. Open PowerPoint and start the slideshow (F5).")
    print(f"  Next slide : http://{ip}:{port}/next")
    print(f"  Prev slide : http://{ip}:{port}/prev")
    print(f"  Phone remote page: http://{ip}:{port}/")
    print(f"  Mi Band page (open in phone Chrome): http://{ip}:{port}/band")
    print("Ctrl+C to stop.\n")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
