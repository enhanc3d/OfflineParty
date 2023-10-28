# Check if Python is installed
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    Write-Output "Python is not installed. Please download and install it from https://www.python.org/downloads/"
    Exit
}

Write-Output "Python is already installed."

# Install packages from requirements.txt
Write-Output "Installing packages from requirements.txt..."
python -m pip install -r .\requirements.txt

Write-Output "Done! Press any key to exit."
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")