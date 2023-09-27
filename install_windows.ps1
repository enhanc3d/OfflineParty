
# Check if Python is installed
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    Write-Output "Python is not installed. Please download and install it from https://www.python.org/downloads/"
    Exit
}

Write-Output "Python is already installed."

# Check and install missing packages
$requirements = Get-Content -Path .\requirements.txt

foreach ($req in $requirements) {
    # Skip empty lines
    if (-not $req) {
        continue
    }
    
    try {
        $module = python -m pip show $req
    } catch {
        $module = $null
    }

    if (-not $module) {
        Write-Output "Installing missing package: $req"
        python -m pip install $req
    } else {
        Write-Output "$req is already installed."
    }
}

Write-Output "Done! Press any key to exit."
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
