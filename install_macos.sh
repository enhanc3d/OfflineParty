#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not found. Installing via Homebrew..."
    brew install python3
else
    echo "Python is already installed."
fi

# Install packages from requirements.txt
echo "Installing packages from requirements.txt..."
pip3 install -r requirements.txt

echo "Done! Press any key to exit."
read -n 1 -s -r