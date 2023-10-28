#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not found. Installing via apt..."
    sudo apt update
    sudo apt install -y python3 python3-pip
else
    echo "Python is already installed."
fi

# Install packages from requirements.txt
echo "Installing packages from requirements.txt..."
python3 -m pip install -r requirements.txt

echo "Done! Press any key to exit."
read -n 1 -s -r