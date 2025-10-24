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
    echo "🐍 Python shell ready — run 'logboard serve logs/app.log'"
  '';
}

