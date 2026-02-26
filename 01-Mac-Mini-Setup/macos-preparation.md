# macOS Preparation for OpenClaw Server

## Overview

This guide walks through preparing a fresh macOS Sequoia installation on a Mac Mini M4 to
serve as a dedicated, always-on OpenClaw agent server. The goal is a headless (or
near-headless) machine that you manage remotely via SSH, with all the development tools
OpenClaw requires pre-installed.

---

## 1. Fresh macOS Sequoia Setup

If starting from a clean install (recommended for a dedicated server):

1. **Complete the Setup Assistant** with a local account or Apple ID
2. **Name the machine** something identifiable: System Settings > General > About > Name
   - Example: `openclaw-server` or `mac-mini-agent`
3. **Enable automatic macOS updates** for security patches:
   - System Settings > General > Software Update > Automatic Updates > toggle all ON
4. **Disable unnecessary visual features** to save resources:
   - System Settings > Accessibility > Display > Reduce Motion: ON
   - System Settings > Desktop & Dock > Minimize windows using: Scale Effect

---

## 2. Homebrew Installation

Homebrew is the package manager for macOS. Almost everything else installs through it.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, Homebrew on Apple Silicon installs to `/opt/homebrew`. Add it to your PATH
by running the commands Homebrew prints at the end of installation:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify the installation:

```bash
brew --version
# Homebrew 4.x.x
```

---

## 3. Essential Packages

Install the core tools OpenClaw and its ecosystem depend on:

```bash
# Core development tools
brew install git
brew install jq           # JSON processing (useful for API debugging)
brew install curl         # Already on macOS but brew version is newer
brew install wget         # Alternative downloader

# Python 3.11+ (needed for some OpenClaw skills and tools)
brew install python@3.12

# Docker Desktop (see docker-installation.md for detailed setup)
brew install --cask docker

# Text editors for config editing over SSH
brew install nano         # Simple editor
brew install vim          # Already on macOS but brew version is newer
```

---

## 4. Node.js 22+ Installation

OpenClaw requires Node.js version 22 or higher. Two approaches:

### Option A: nvm (Recommended - allows version switching)

```bash
# Install nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# Reload shell configuration
source ~/.zshrc

# Install Node.js 22 (LTS)
nvm install 22

# Set it as default
nvm alias default 22

# Verify
node --version   # Should print v22.x.x
npm --version    # Should print 10.x.x or higher
```

**Why nvm?** If OpenClaw ever requires a different Node version, or you want to test against
Node 23+, nvm lets you switch instantly with `nvm use <version>`.

### Option B: Homebrew (Simpler, single version)

```bash
brew install node@22

# Add to PATH (Homebrew does not link keg-only formulae by default)
echo 'export PATH="/opt/homebrew/opt/node@22/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
node --version   # Should print v22.x.x
```

### Option C: Volta (Alternative version manager)

```bash
brew install volta
volta install node@22

# Verify
node --version   # v22.x.x
```

---

## 5. Python 3.11+ Setup

Some OpenClaw skills (web scraping, data processing, ML integrations) invoke Python scripts.

```bash
# Verify Python installed via brew
python3 --version   # Should print Python 3.12.x

# Install pip packages commonly needed by OpenClaw skills
pip3 install --user requests beautifulsoup4 numpy pandas

# Create a virtual environment for OpenClaw-related Python work
python3 -m venv ~/openclaw-python-env
echo 'alias ocpy="source ~/openclaw-python-env/bin/activate"' >> ~/.zshrc
```

---

## 6. Shell Configuration (.zshrc)

macOS Sequoia uses zsh as the default shell. Set up a clean `.zshrc` with all the paths and
aliases you need:

```bash
# Edit .zshrc
nano ~/.zshrc
```

Add the following block (adjust to match your actual installations):

```bash
# =============================================================================
# OpenClaw Server - Shell Configuration
# =============================================================================

# --- Homebrew ---
eval "$(/opt/homebrew/bin/brew shellenv)"

# --- Node.js via nvm ---
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# --- Python ---
export PATH="$HOME/Library/Python/3.12/bin:$PATH"

# --- OpenClaw Aliases ---
alias oc-start="cd ~/openclaw && docker compose up -d"
alias oc-stop="cd ~/openclaw && docker compose down"
alias oc-logs="cd ~/openclaw && docker compose logs -f"
alias oc-restart="cd ~/openclaw && docker compose restart"
alias oc-status="docker compose -f ~/openclaw/docker-compose.yml ps"
alias oc-health="curl -s http://localhost:18789/health | jq ."

# --- Ollama Aliases ---
alias ollama-models="ollama list"
alias ollama-run="ollama serve &"

# --- General Server Aliases ---
alias ports="lsof -i -P -n | grep LISTEN"
alias myip="ifconfig en0 | grep 'inet ' | awk '{print \$2}'"
alias diskfree="df -h / | tail -1 | awk '{print \$4 \" free of \" \$2}'"
alias memfree="memory_pressure | head -1"

# --- History Configuration ---
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
```

Apply changes:

```bash
source ~/.zshrc
```

---

## 7. Energy Settings (Prevent Sleep)

A 24/7 server must never sleep. Configure macOS to stay awake permanently.

### Via System Settings UI:
1. System Settings > Energy (or Battery > Energy on some versions)
2. Set "Turn display off after" to a short time (5 minutes is fine; display off does not mean sleep)
3. Toggle ON: "Prevent automatic sleeping when the display is off"
4. Toggle ON: "Wake for network access"
5. Toggle ON: "Start up automatically after a power failure"

### Via Terminal (pmset):

```bash
# Prevent sleep entirely
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 5     # Display can sleep, machine stays awake

# Wake on network access (Wake-on-LAN)
sudo pmset -a womp 1

# Restart automatically after power failure
sudo pmset -a autorestart 1

# Verify settings
pmset -g
```

### Scheduled Weekly Restart (Recommended)

A weekly restart clears accumulated memory leaks and keeps the system fresh:

```bash
# Schedule restart every Sunday at 4:00 AM
# Create a launchd plist for scheduled restart
sudo bash -c 'cat > /Library/LaunchDaemons/com.openclaw.weekly-restart.plist << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.weekly-restart</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/shutdown</string>
        <string>-r</string>
        <string>now</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
PLIST'

sudo launchctl load /Library/LaunchDaemons/com.openclaw.weekly-restart.plist
```

Alternatively, use the simpler approach in System Settings > General > Startup & Shutdown >
Schedule (if available on your macOS version).

---

## 8. SSH Setup for Remote Management

SSH is essential for managing a headless Mac Mini from your main workstation.

### Enable SSH (Remote Login):

1. System Settings > General > Sharing
2. Toggle ON: "Remote Login"
3. Allow access for: "Only these users" > add your user account
   (More secure than "All users")

### From your main machine, connect:

```bash
ssh yourusername@mac-mini-ip
# Example: ssh admin@192.168.1.100
```

### Set up SSH key authentication (passwordless, more secure):

On your main machine:

```bash
# Generate a key pair if you do not have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy your public key to the Mac Mini
ssh-copy-id yourusername@mac-mini-ip
```

### Harden SSH (optional but recommended):

On the Mac Mini, edit the SSH config:

```bash
sudo nano /etc/ssh/sshd_config
```

Recommended changes:

```
# Disable password authentication (key-only)
PasswordAuthentication no

# Disable root login
PermitRootLogin no

# Only allow your user
AllowUsers yourusername
```

Restart SSH:

```bash
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

### SSH Config on Your Main Machine

Add to `~/.ssh/config` on your daily driver for easy access:

```
Host openclaw
    HostName 192.168.1.100
    User yourusername
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Now you can simply run: `ssh openclaw`

---

## 9. Screen Sharing / VNC for GUI Access

Sometimes you need a GUI (Docker Desktop settings, browser testing, etc.).

### Enable Screen Sharing:

1. System Settings > General > Sharing
2. Toggle ON: "Screen Sharing"
3. Allow access for your user account
4. Note the VNC address shown (e.g., `vnc://192.168.1.100`)

### Connect from another Mac:

- Finder > Go > Connect to Server > `vnc://192.168.1.100`
- Or use the "Screen Sharing" app (in /System/Library/CoreServices/Applications/)

### Connect from Windows:

- Use RealVNC Viewer or TightVNC Viewer
- Connect to `192.168.1.100:5900`

### Connect from Linux:

```bash
# Using Remmina or vinagre
vinagre vnc://192.168.1.100:5900
```

### Performance tip:

Screen sharing uses bandwidth. For day-to-day management, prefer SSH. Reserve screen sharing
for when you genuinely need the GUI (Docker Desktop configuration, debugging visual issues).

---

## 10. Firewall Configuration

Enable the macOS firewall but allow OpenClaw-related services:

```bash
# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow SSH
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd

# Allow Node.js (for OpenClaw native install)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which node)

# Allow Ollama
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/ollama

# Check status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

---

## Checklist

After completing this guide, verify:

- [ ] Homebrew installed and on PATH: `brew --version`
- [ ] Git installed: `git --version`
- [ ] Node.js 22+ installed: `node --version` (should show v22.x.x)
- [ ] npm available: `npm --version`
- [ ] Python 3.11+ installed: `python3 --version`
- [ ] Docker Desktop installed: `docker --version`
- [ ] SSH enabled and tested from another machine
- [ ] Energy settings configured (no sleep)
- [ ] .zshrc configured with paths and aliases
- [ ] Firewall enabled with exceptions

---

## Next Steps

- [Ollama Local Models](ollama-local-models.md) - Set up local LLM inference
- [Docker Installation](docker-installation.md) - Deploy OpenClaw via Docker
- [Native Installation](native-installation.md) - Deploy OpenClaw via npm
