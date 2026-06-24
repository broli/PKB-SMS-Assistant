#!/bin/bash

# Create the local windows_build directory if it doesn't exist
mkdir -p "/home/carlos/Projects/Antigravity/PKB-SMS-Assistant/windows_build"

echo -e "\e[36mPulling the compiled Windows executable from the VM...\e[0m"

# Use SCP to copy the .exe directly from the VM's dist folder into the local windows_build folder
# Assuming the VM project path is C:/Users/Work/Documents/GitHub/PKB-SMS-Assistant
scp work@192.168.122.216:"C:/Users/Work/Documents/GitHub/PKB-SMS-Assistant/dist/*.exe" "/home/carlos/Projects/Antigravity/PKB-SMS-Assistant/windows_build/"

if [ $? -eq 0 ]; then
    echo -e "\e[32mSuccessfully pulled the executable! It is now located in your local windows_build/ directory.\e[0m"
else
    echo -e "\e[31mFailed to pull the executable. Ensure the VM is running and the path is correct.\e[0m"
    exit 1
fi
