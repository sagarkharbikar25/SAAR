# main.py
import sys
import traceback

if __name__ == "__main__":
    try:
        print("[EXE DEBUG] Initializing Neural Core...")
        from ui.main_window import run_app
        print("[EXE DEBUG] UI Module Loaded. Launching...")
        run_app()
    except (KeyboardInterrupt, SystemExit):
        print("\n🚀 [Neural Core] Graceful shutdown initiated. Goodbye Sagar.")
        sys.exit(0)
    except Exception as e:
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        print(f"CRITICAL ERROR: {e}")
        input("Press Enter to close...")
