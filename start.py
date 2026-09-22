import os
import sys

# Configure UTF-8 encoding for standard output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import webbrowser
import time
import uvicorn

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print("=" * 65)
    print("  [*] Amazon Ops Copilot Starting...")
    print(f"  [*] Dashboard URL: {url}")
    print("  [*] Data Source: SellerSprite MCP Official Server")
    print("=" * 65)
    
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    app_module = "backend.main:app"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    uvicorn.run(
        app_module,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
