#!/bin/bash

echo -e "\e[36mBuilding PKB SMS Assistant...\e[0m"

# Remove old executable if it exists to ensure we get a fresh build
if [ -f "./dist/PKB SMS Assistant" ]; then
    echo -e "\e[33mCleaning up old build...\e[0m"
    rm -f "./dist/PKB SMS Assistant"
fi

# Use the python binary in the virtual environment to run pyinstaller
source ./.venv/bin/activate
pyinstaller main.spec --noconfirm

# Check if build was successful
if [ $? -eq 0 ] && [ -f "./dist/PKB SMS Assistant" ]; then
    echo -e "\e[32mBuild completed successfully! The executable is located in the 'dist' folder.\e[0m"
else
    echo -e "\e[31mBuild failed. Please check the output above for errors.\e[0m"
    exit 1
fi
