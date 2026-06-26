#!/bin/bash

# PKB SMS Assistant - Distribution Orchestrator

NOBUILD=true

for arg in "$@"; do
    if [ "$arg" == "--build" ]; then
        NOBUILD=false
    fi
done

echo -e "\e[36m--------------------------------------------------\e[0m"
echo -e "\e[36mStarting Cross-Platform Distribution\e[0m"
if [ "$NOBUILD" = true ]; then
    echo -e "\e[33mBuild Mode: SKIPPED (--nobuild)\e[0m"
fi
echo -e "\e[36m--------------------------------------------------\e[0m"

# 1. Build Linux Executable
if [ "$NOBUILD" = false ]; then
    ./build.sh
    if [ $? -ne 0 ]; then
        echo -e "\e[31mError: Linux Build failed. Distribution aborted.\e[0m"
        exit 1
    fi
fi

# Verify Linux executable exists
LINUX_EXE="./dist/PKB SMS Assistant"
if [ ! -f "$LINUX_EXE" ]; then
    echo -e "\e[31mDistribution aborted: Linux executable not found in 'dist/'.\e[0m"
    exit 1
fi

TARGET_NAME="PKB SMS Assistant"

# 2. Setup Staging for Rclone
echo -e "\e[36mSetting up staging area for SharePoint Sync...\e[0m"
TMP_STAGE="/tmp/pkb_sms_stage"
mkdir -p "$TMP_STAGE"
rm -rf "$TMP_STAGE/*"

# Copy Linux build to staging
cp -f "$LINUX_EXE" "$TMP_STAGE/$TARGET_NAME"

# Copy documentation
DOCS=("README.md" "walkthrough.md")
for doc in "${DOCS[@]}"; do
    if [ -f "./$doc" ]; then
        cp -f "./$doc" "$TMP_STAGE/"
    fi
done

# Copy Windows executable if available
WINDOWS_EXE="./windows_build/PKB SMS Assistant.exe"
if [ -f "$WINDOWS_EXE" ]; then
    echo -e "\e[36mFound Windows executable! Including it in the distribution...\e[0m"
    cp -f "$WINDOWS_EXE" "$TMP_STAGE/"
else
    echo -e "\e[33mWarning: No Windows executable found in 'windows_build/'. Proceeding with Linux build only.\e[0m"
    echo -e "\e[33mTip: Run ./pull_windows_build.sh to grab it from your VM.\e[0m"
fi

# 3. Perform Rclone Sync
echo -e "\e[36mSyncing to SharePoint (PKBspBathPC:PKB SMS Assistant)...\e[0m"
rclone sync "$TMP_STAGE" "PKBspBathPC:PKB SMS Assistant" --exclude "corporate_config.*" --exclude "*.tmp" --progress

if [ $? -ne 0 ]; then
    echo -e "\e[31mError: Rclone sync to SharePoint failed.\e[0m"
    exit 1
fi

# Cleanup
rm -rf "$TMP_STAGE"

echo -e "\e[32m--------------------------------------------------\e[0m"
echo -e "\e[32mDistribution Successful!\e[0m"
echo -e "\e[32mSharePoint Sync Complete.\e[0m"
echo -e "\e[32m--------------------------------------------------\e[0m"
