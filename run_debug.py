import traceback

try:
    from src.game import Game

    Game().run()
except SystemExit:
    pass
except Exception:
    with open("crash_log.txt", "w") as f:
        f.write(traceback.format_exc())
    print("=== CRASH ===")
    print(traceback.format_exc())
    input("Press Enter to close...")
