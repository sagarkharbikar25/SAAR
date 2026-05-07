import os
import subprocess
import shutil

def build():
    # 1. Install PyInstaller if not present
    print("[BUILD] Verifying PyInstaller...")
    subprocess.run(["pip", "install", "pyinstaller"], check=True)

    # 2. Define Command
    # We include all essential folders and use --collect-all for customtkinter
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--add-data", "ui;ui/",
        "--add-data", "avatar;avatar/",
        "--add-data", "voice;voice/",
        "--add-data", "core;core/",
        "--add-data", "pipeline;pipeline/",
        "--add-data", "features;features/",
        "--add-data", "data;data/",
        "--add-data", "database;database/",
        "--add-data", "saar.db*;.",
        "--add-data", "C:/Users/asus/AppData/Local/Programs/Python/Python311/Lib/site-packages/face_recognition_models/models/*;face_recognition_models/models/",
        "--collect-all", "customtkinter",
        "--collect-all", "face_recognition",
        "--collect-all", "face_recognition_models",
        "main.py"
    ]

    print(f"[BUILD] Starting build process for SAAR Elite HUD...")
    subprocess.run(cmd, check=True)
    
    print("\n" + "="*50)
    print("BUILD COMPLETE!")
    print(f"You can find your EXE in: {os.path.join(os.getcwd(), 'dist', 'main', 'main.exe')}")
    print("="*50)

if __name__ == "__main__":
    build()
