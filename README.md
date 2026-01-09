# SPSS Win Wrapper

Launch IBM SPSS Statistics (Windows) through Bottles on Linux from the command line.

**Tested with:** IBM SPSS Statistics 31.0.1

## Prerequisites

- Linux with Flatpak installed
- [Bottles](https://usebottles.com/) installed via Flatpak
- IBM SPSS Statistics installed in a Bottles bottle
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
# With uv (recommended)
uv tool install git+https://github.com/mtr/spss-win-wrapper.git

# Or with pip
pip install git+https://github.com/mtr/spss-win-wrapper.git
```

## Quick Start

```bash
# Launch SPSS
spss

# Open a file in SPSS
spss data.sav

# Open multiple files
spss data.sav analysis.spv
```

## Configuration

The wrapper needs to know which Bottles bottle contains SPSS. Configure this in one of three ways (in order of priority):

### 1. Command-line flags

```bash
spss --bottle "My SPSS Bottle" --program "SPSS Statistics" data.sav
```

### 2. Environment variables

```bash
export SPSS_BOTTLE_NAME="My SPSS Bottle"
export SPSS_PROGRAM_NAME="SPSS Statistics"
spss data.sav
```

### 3. Config file

Create a config file at `~/.config/spss-wrapper/config.toml`:

```bash
# Generate config file with current settings
spss --init-config

# Or with custom values
spss --bottle "My SPSS Bottle" --program "SPSS Statistics" --init-config
```

Config file format:

```toml
bottle_name = "SPSS"
program_name = "SPSS"
flatpak_app_id = "com.usebottles.bottles"
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--bottle` | `-b` | Bottle name containing SPSS |
| `--program` | `-p` | Program name within the bottle |
| `--flatpak-app-id` | | Flatpak app ID for Bottles |
| `--verbose` | `-v` | Show detailed output |
| `--dry-run` | `-n` | Show command without executing |
| `--init-config` | | Create config file and exit |
| `--force` | `-f` | Overwrite existing config file |
| `--show-output` | | Show Bottles/Wine output in terminal |

## Logging

By default, Bottles/Wine output is redirected to log files at:

```
~/.local/share/spss-wrapper/logs/spss_YYYYMMDD_HHMMSS.log
```

Use `--show-output` to display output in the terminal instead, or `--verbose` to see which log file is being used.

## Setting Up SPSS in Bottles

1. Install Bottles from Flathub:
   ```bash
   flatpak install flathub com.usebottles.bottles
   ```

2. Create a new bottle (e.g., named "SPSS")

3. Install IBM SPSS Statistics in the bottle

4. Add SPSS as a program in the bottle's settings (note the program name you use)

5. Configure the wrapper:
   ```bash
   spss --bottle "SPSS" --program "SPSS" --init-config
   ```

## Troubleshooting

**"Bottle does not exist" error:**
```bash
# List available bottles
flatpak run --command=bottles-cli com.usebottles.bottles list bottles
```

**"flatpak command not found":**
```bash
# Install Flatpak
# Ubuntu/Debian
sudo apt install flatpak

# Fedora
sudo dnf install flatpak

# Arch
sudo pacman -S flatpak
```

**Path translation fails:**

The wrapper uses `winepath` inside the bottle to convert Linux paths to Windows paths. Ensure the file is accessible from within the bottle (typically paths under your home directory work).

## License

MIT
