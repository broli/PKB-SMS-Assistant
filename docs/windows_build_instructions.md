# Windows Build Instructions

This guide explains how to compile the Windows version of the **PKB SMS Assistant** from within your Windows VM and sync it to SharePoint.

## Prerequisites
1. A running Windows Virtual Machine (e.g., KVM via `virt-manager`).
2. Python installed on the Windows VM.
3. The project cloned/copied to your Windows VM (e.g., in `C:\Users\Work\Documents\GitHub\PKB-SMS-Assistant`).

## Step 1: Prepare the Windows Environment
Log into your Windows VM and open a PowerShell terminal inside the project folder.

1. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```
2. **Activate it:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   pip install pyinstaller
   ```

## Step 2: Build the Executable
Still in PowerShell on your Windows VM, run the build script:
```powershell
.\build.ps1
```
*This will clean up any old builds, run PyInstaller using `windows_build.spec`, and output the new `PKB SMS Assistant.exe` into the `dist` folder.*

## Step 3: Pull to Linux Host
You don't need to manually copy the file out of the VM! Go back to your **Linux host machine**, open a terminal in the project folder, and run:
```bash
./pull_windows_build.sh
```
*This will use SSH/SCP to securely yank the `.exe` out of your VM's `dist` folder and place it into your local `windows_build/` folder.*

## Step 4: Distribute to SharePoint
Finally, run the master distribution script on your Linux host:
```bash
./distribute.sh
```
*This script will compile the Linux version, collect the Windows version from `windows_build/`, and sync everything straight to your company SharePoint!*
