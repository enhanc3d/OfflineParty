
#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python is not found. Installing via apt..."
    sudo apt update
    sudo apt install -y python3 python3-pip
else
    echo "Python is already installed."
fi

# Check and install missing packages
while IFS= read -r requirement; do
    # Skip empty lines
    if [ -z "$requirement" ]; then
        continue
    fi
    
    python3 -m pip show "$requirement" &> /dev/null
    if [ $? -ne 0 ]; then
        echo "Installing missing package: $requirement"
        python3 -m pip install "$requirement"
    else
        echo "$requirement is already installed."
    fi
done < requirements.txt

echo "Done! Press any key to exit."
read -n 1 -s -r
