"""CLI wrapper for launching IBM SPSS through Bottles on Linux."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

# Use tomllib from stdlib in Python 3.11+, otherwise fall back to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Default configuration values
DEFAULT_BOTTLE_NAME = 'SPSS'
DEFAULT_PROGRAM_NAME = 'SPSS'
DEFAULT_FLATPAK_APP_ID = 'com.usebottles.bottles'
CONFIG_FILE_PATH = Path.home() / '.config' / 'spss-wrapper' / 'config.toml'


@dataclass
class Config:
    """Configuration for the SPSS wrapper."""

    bottle_name: str
    program_name: str
    flatpak_app_id: str


def load_config_file() -> dict[str, str]:
    """Load configuration from the config file if it exists."""
    if not CONFIG_FILE_PATH.exists():
        return {}

    try:
        with CONFIG_FILE_PATH.open('rb') as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        typer.echo(
            f'Warning: Failed to read config file {CONFIG_FILE_PATH}: {e}',
            err=True,
        )
        return {}


def create_config_file(
    bottle_name: str,
    program_name: str,
    flatpak_app_id: str,
    force: bool = False,
) -> None:
    """Create the config file with the specified values."""
    if CONFIG_FILE_PATH.exists() and not force:
        typer.echo(f'Config file already exists: {CONFIG_FILE_PATH}', err=True)
        typer.echo('Use --force to overwrite.', err=True)
        raise typer.Exit(1)

    # Create parent directory if it doesn't exist
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    config_content = f'''# SPSS Wrapper Configuration
# Values here are overridden by environment variables and CLI flags.

bottle_name = "{bottle_name}"
program_name = "{program_name}"
flatpak_app_id = "{flatpak_app_id}"
'''

    try:
        CONFIG_FILE_PATH.write_text(config_content)
        typer.echo(f'Created config file: {CONFIG_FILE_PATH}')
    except OSError as e:
        typer.echo(f'Error: Failed to create config file: {e}', err=True)
        raise typer.Exit(1)


def get_config(
    bottle_override: str | None = None,
    program_override: str | None = None,
    flatpak_app_id_override: str | None = None,
) -> Config:
    """Get configuration with priority: CLI flags > env vars > config file > defaults."""
    file_config = load_config_file()

    bottle_name = (
        bottle_override
        or os.environ.get('SPSS_BOTTLE_NAME')
        or file_config.get('bottle_name')
        or DEFAULT_BOTTLE_NAME
    )

    program_name = (
        program_override
        or os.environ.get('SPSS_PROGRAM_NAME')
        or file_config.get('program_name')
        or DEFAULT_PROGRAM_NAME
    )

    flatpak_app_id = (
        flatpak_app_id_override
        or os.environ.get('BOTTLES_FLATPAK_APP_ID')
        or file_config.get('flatpak_app_id')
        or DEFAULT_FLATPAK_APP_ID
    )

    return Config(
        bottle_name=bottle_name,
        program_name=program_name,
        flatpak_app_id=flatpak_app_id,
    )


def resolve_and_validate_path(file_path: str) -> Path:
    """Resolve a path to absolute and validate that it exists."""
    path = Path(file_path).resolve()

    if not path.exists():
        typer.echo(f'Error: File does not exist: {path}', err=True)
        raise typer.Exit(1)

    return path


def translate_path_to_windows(
    linux_path: Path,
    config: Config,
    verbose: bool = False,
) -> str:
    """Translate a Linux path to a Windows path using winepath in the bottle."""
    cmd = [
        'flatpak',
        'run',
        '--command=bottles-cli',
        config.flatpak_app_id,
        'shell',
        '-b',
        config.bottle_name,
        '-i',
        f"winepath -w '{linux_path}'",
    ]

    if verbose:
        typer.echo(f'Running winepath command: {" ".join(cmd)}')

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        windows_path = result.stdout.strip()

        if not windows_path:
            typer.echo(
                f'Error: winepath returned empty result for {linux_path}\n\n'
                'This may indicate:\n'
                '  - The bottle is not properly configured\n'
                '  - The path is not accessible from within the bottle\n\n'
                'Try running manually:\n'
                f'  flatpak run --command=bottles-cli {config.flatpak_app_id} '
                f'shell -b {config.bottle_name} -i "winepath -w \'{linux_path}\'"',
                err=True,
            )
            raise typer.Exit(1)

        return windows_path

    except subprocess.CalledProcessError as e:
        typer.echo(
            f"Error: Failed to translate path '{linux_path}' to Windows format.\n\n"
            f'Command failed with exit code {e.returncode}\n'
            f'stdout: {e.stdout}\n'
            f'stderr: {e.stderr}\n\n'
            'Possible causes:\n'
            f"  - Bottle '{config.bottle_name}' does not exist\n"
            '  - Bottles/Flatpak is not properly installed\n'
            '  - The flatpak app ID may be incorrect\n\n'
            'To check available bottles, run:\n'
            f'  flatpak run --command=bottles-cli {config.flatpak_app_id} list bottles',
            err=True,
        )
        raise typer.Exit(1)

    except FileNotFoundError:
        typer.echo(
            "Error: 'flatpak' command not found.\n\n"
            'Please ensure Flatpak is installed:\n'
            '  Ubuntu/Debian: sudo apt install flatpak\n'
            '  Fedora: sudo dnf install flatpak\n'
            '  Arch: sudo pacman -S flatpak',
            err=True,
        )
        raise typer.Exit(1)


def build_spss_command(
    config: Config,
    windows_paths: list[str],
) -> list[str]:
    """Build the command to launch SPSS with the given files."""
    cmd = [
        'flatpak',
        'run',
        '--command=bottles-cli',
        config.flatpak_app_id,
        'run',
        '-b',
        config.bottle_name,
        '-p',
        config.program_name,
    ]

    if windows_paths:
        cmd.extend(windows_paths)

    return cmd


app = typer.Typer(
    help='Launch IBM SPSS through Bottles on Linux.',
    add_completion=False,
)


@app.command()
def main(
    files: Annotated[
        list[str] | None,
        typer.Argument(
            help='Files to open in SPSS (optional). Accepts any file type SPSS can open.',
        ),
    ] = None,
    bottle: Annotated[
        str | None,
        typer.Option(
            '--bottle',
            '-b',
            help='Bottle name to use (overrides env var and config file).',
        ),
    ] = None,
    program: Annotated[
        str | None,
        typer.Option(
            '--program',
            '-p',
            help='Program name within the bottle (overrides env var and config file).',
        ),
    ] = None,
    flatpak_app_id: Annotated[
        str | None,
        typer.Option(
            '--flatpak-app-id',
            help='Flatpak app ID for Bottles (overrides env var and config file).',
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            '--verbose',
            '-v',
            help='Show detailed output including commands being run.',
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            '--dry-run',
            '-n',
            help='Show the command that would be executed without running it.',
        ),
    ] = False,
    init_config: Annotated[
        bool,
        typer.Option(
            '--init-config',
            help='Create config file with current settings and exit.',
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            '--force',
            '-f',
            help='Overwrite existing config file when using --init-config.',
        ),
    ] = False,
) -> None:
    """Launch IBM SPSS through Bottles, optionally opening files."""
    config = get_config(
        bottle_override=bottle,
        program_override=program,
        flatpak_app_id_override=flatpak_app_id,
    )

    if init_config:
        create_config_file(
            bottle_name=config.bottle_name,
            program_name=config.program_name,
            flatpak_app_id=config.flatpak_app_id,
            force=force,
        )
        return

    if verbose:
        typer.echo('Configuration:')
        typer.echo(f'  Bottle: {config.bottle_name}')
        typer.echo(f'  Program: {config.program_name}')
        typer.echo(f'  Flatpak App ID: {config.flatpak_app_id}')

    windows_paths: list[str] = []

    if files:
        for file_path in files:
            linux_path = resolve_and_validate_path(file_path)

            if verbose:
                typer.echo(f'Resolved path: {file_path} -> {linux_path}')

            windows_path = translate_path_to_windows(
                linux_path, config, verbose
            )

            if verbose:
                typer.echo(f'Windows path: {windows_path}')

            windows_paths.append(windows_path)

    cmd = build_spss_command(config, windows_paths)

    if dry_run or verbose:
        typer.echo(f'Command: {" ".join(cmd)}')

    if dry_run:
        return

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        typer.echo(f'Error: SPSS exited with code {e.returncode}', err=True)
        raise typer.Exit(e.returncode)
    except FileNotFoundError:
        typer.echo(
            "Error: 'flatpak' command not found.\n\n"
            'Please ensure Flatpak is installed:\n'
            '  Ubuntu/Debian: sudo apt install flatpak\n'
            '  Fedora: sudo dnf install flatpak\n'
            '  Arch: sudo pacman -S flatpak',
            err=True,
        )
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
