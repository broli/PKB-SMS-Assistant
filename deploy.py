import os
import shutil
import sys

# Configuration
TARGET_DIR = r"C:\Users\carlo\Desktop\PKB Apps\SMS Companion"
EXE_SOURCE = r"dist\PKB SMS Assistant.exe"
DATA_FILES = ["config.dat", "contacts.json"]

def deploy():
    print("=" * 50)
    print("PKB SMS Assistant Deployment Script")
    print("=" * 50)

    # 1. Ensure target directory exists
    if not os.path.exists(TARGET_DIR):
        print(f"[*] Creating target directory: {TARGET_DIR}")
        try:
            os.makedirs(TARGET_DIR, exist_ok=True)
        except Exception as e:
            print(f"[!] Error creating directory: {e}")
            return

    # 2. Copy the Executable
    if os.path.exists(EXE_SOURCE):
        target_exe = os.path.join(TARGET_DIR, "PKB SMS Assistant.exe")
        print(f"[*] Copying executable to: {TARGET_DIR}")
        try:
            shutil.copy2(EXE_SOURCE, target_exe)
            print("    [+] EXE copied successfully.")
        except Exception as e:
            print(f"    [!] Error copying EXE: {e}")
            return
    else:
        print(f"[!] Error: Source EXE not found at '{EXE_SOURCE}'")
        print("    Please run the PyInstaller build first.")
        return

    # 3. Handle Optional Data Files
    print("-" * 50)
    for f in DATA_FILES:
        if os.path.exists(f):
            # We ask the user for confirmation
            try:
                # Use sys.stdin.flush() to avoid potential buffer issues
                print(f"\n[?] Found local '{f}'.")
                choice = input(f"    Do you want to copy it to the deployment folder? (y/n): ").lower().strip()
                
                if choice == 'y':
                    dest_f = os.path.join(TARGET_DIR, f)
                    if os.path.exists(dest_f):
                        print(f"    [!] Warning: '{f}' already exists in target. Overwriting...")
                    
                    shutil.copy2(f, dest_f)
                    print(f"    [+] {f} deployed.")
                else:
                    print(f"    [ ] Skipping {f}.")
            except EOFError:
                # Fallback for non-interactive environments
                print(f"    [ ] Skipping {f} (Non-interactive environment).")
        else:
            print(f"[ ] Local '{f}' not found, skipping.")

    print("\n" + "=" * 50)
    print("Deployment Complete!")
    print(f"Location: {TARGET_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    deploy()
