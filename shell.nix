{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.fastapi
    pkgs.python3Packages.uvicorn
    pkgs.python3Packages.jinja2
    pkgs.python3Packages.typer
    pkgs.python3Packages.pip
  ];

  shellHook = ''
    # Create virtual environment if it doesn't exist
    if [ ! -d .venv ]; then
      echo "Creating virtual environment..."
      python -m venv .venv
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Upgrade pip and install the project in editable mode
    pip install --upgrade pip > /dev/null 2>&1
    if [ -f setup.py ] || [ -f pyproject.toml ]; then
      pip install -e . > /dev/null 2>&1
    fi

    echo "🐍 Python virtual environment activated — run 'logboard serve logs/app.log'"
  '';
}

