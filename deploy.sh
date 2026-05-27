#!/bin/bash

echo -e "\e[36mStarting Build and Deploy process...\e[0m"

# Run the build script
./build.sh

# Verify the executable exists before trying to copy
if [ ! -f "./dist/PKB SMS Assistant" ]; then
    echo -e "\e[31mDeployment aborted because the build failed or the executable was not found.\e[0m"
    exit 1
fi

targetDir="$HOME/.local/bin"
appsDir="$HOME/.local/share/applications"
iconsDir="$HOME/.local/share/icons"

echo -e "\e[36mDeploying executable to $targetDir...\e[0m"

# Create directories if they don't exist
mkdir -p "$targetDir"
mkdir -p "$appsDir"
mkdir -p "$iconsDir"

# Copy the executable
cp -f "./dist/PKB SMS Assistant" "$targetDir/PKB SMS Assistant"

if [ $? -ne 0 ]; then
    echo -e "\e[31mFailed to copy the executable.\e[0m"
    echo -e "\e[33mMake sure the application is closed before deploying.\e[0m"
    exit 1
fi

# Copy the icon
cp -f "./app.ico" "$iconsDir/pkb-sms-assistant.ico"

# Create the .desktop file
desktopFile="$appsDir/pkb-sms-assistant.desktop"
echo -e "\e[36mCreating desktop entry at $desktopFile...\e[0m"

cat > "$desktopFile" << EOL
[Desktop Entry]
Version=1.0
Name=PKB SMS Assistant
Comment=Desktop application to manage and interact with SMS
Exec="$targetDir/PKB SMS Assistant"
Icon=$iconsDir/pkb-sms-assistant.ico
Terminal=false
Type=Application
Categories=Utility;Communication;
EOL

chmod +x "$desktopFile"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$appsDir"
fi

echo -e "\e[32mDeployment successful!\e[0m"
echo -e "\e[32mExecutable copied to: $targetDir/PKB SMS Assistant\e[0m"
echo -e "\e[32mDesktop entry created: $desktopFile\e[0m"
