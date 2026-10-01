<p align="center">
  <img src="kiro.jpg" alt="Kiro" width="220" />
</p>

# ArchLinux Logout GTK4

A modern, customizable logout/power management widget for ArchLinux and other Linux distributions. Built with GTK4, this application provides a transparent, fullscreen overlay for quick access to power management features with an elegant, theme-aware interface.

# Installation

Add the nemesis_repo to your /etc/pacman.conf and update your system.

```
[nemesis_repo]
SigLevel = Never
Server = https://erikdubois.github.io/$repo/$arch
```

Then install 

```
sudo pacman -S archlinux-logout
```

## Overview

ArchLinux Logout is a power management utility designed for desktop environments and window managers that need a unified way to access logout, shutdown, reboot, suspend, hibernate, and lock functionality. The application displays a beautiful, semi-transparent window with large, easy-to-click icons and optional labels for each action.

## Dependencies

This application requires the following packages:

```bash
depends=('python-psutil' 'libwnck3' 'python-cairo' 'betterlockscreen' 'python-distro')
```

### Dependency Details

- **python-psutil**: For system monitoring and process handling
- **libwnck3**: Window manager utilities for detecting desktop environment
- **python-cairo**: Graphics rendering library for custom drawings
- **betterlockscreen**: Advanced lockscreen functionality with blur effects
- **python-distro**: For detecting the Linux distribution and session type

## Features

### Power Management Actions

The application provides quick access to the following power management features via buttons and keyboard shortcuts:

- **Logout (L)** - Exit the current desktop session
- **Reboot/Restart (R)** - Restart the system
- **Shutdown (S)** - Power off the system
- **Suspend (U)** - Put the system into sleep mode
- **Hibernate (H)** - Save system state to disk and power off
- **Lock (K)** - Lock the current session

### Customization Options

ArchLinux Logout offers extensive configuration options to personalize the appearance and behavior:

- **Widget Opacity**: Control the transparency level of the overlay (0-100%)
- **Icon Size**: Adjust the size of action icons to suit your preferences (defaults to 80px)
- **Font Size**: Customize the size of action labels
- **Theme Selection**: Choose from multiple built-in themes to match your desktop aesthetic
- **Button Visibility**: Show or hide specific power management buttons
- **Text Labels**: Toggle whether action labels are displayed alongside icons

## Configuration

### Config Location

Configuration is stored in: `~/.config/archlinux-logout/archlinux-logout.conf`

On first run, the default configuration is automatically copied from `/etc/archlinux-logout.conf`.

### Configuration File Format

The config file uses INI-style format with the following sections:

```bash
[settings]
opacity=80
icon_size=80
font_size=11
theme=handy
show_text=False
buttons=cancel,shutdown,restart,suspend,hibernate,lock,logout

[commands]
lock=betterlockscreen -l dim -- --time-str="%H:%M"
shutdown=systemctl poweroff
restart=systemctl reboot
suspend=systemctl suspend
hibernate=systemctl hibernate

[binds]
lock=K
restart=R
shutdown=S
suspend=U
hibernate=H
logout=L
cancel=Escape
settings=P

[themes]
theme=handy
```

### Display Detection

The application automatically detects:

- **Session Type**: Distinguishes between Wayland and X11 sessions
- **Monitor Layout**: On X11, uses xdotool to detect mouse position and display the logout menu on the correct monitor
- **Desktop Environment**: Automatically selects appropriate logout commands for different DEs and window managers



## Keyboard Shortcuts

All power management actions and settings can be accessed via keyboard:

- **S** - Shutdown
- **R** - Restart/Reboot
- **U** - Suspend
- **H** - Hibernate
- **K** - Lock
- **L** - Logout
- **P** - Settings/Preferences
- **Escape** - Cancel

### Settings Panel

Press **P** to open the settings panel, where you can:
- Adjust widget opacity with a slider
- Modify icon size
- Change font size
- Select a theme
- Toggle text labels
- Enable/disable specific buttons
- Save your preferences

## Themes

ArchLinux Logout includes **30 built-in themes** to match your desktop aesthetic and personal preferences. Themes are located in `/usr/share/archlinux-logout-themes/themes/` and each provides a complete set of SVG icons for all power management actions.

### Available Themes

The following themes are available, organized by style:

**Color-Accent Themes:**

- **handy** - Golden/tan accent (#ffd397)
- **neocandy** - Golden/tan accent with modern styling
- **sweet** - Golden/tan accent with softer appearance
- **orange** - Warm orange accent
- **yellow** - Bright yellow accent
- **red** - Bold red accent (crimson)
- **blue** - Cool blue accent (dodgerblue)

**White/Neutral Themes:**

- beauty
- breeze
- breeze-blur
- candy
- runes
- surfn
- white

**Sardi Icon Pack Themes** (18 variants):

- sardi-blood
- sardi-blue
- sardi-botticelli
- sardi-candy
- sardi-emerald
- sardi-evopop
- sardi-faba
- sardi-fire
- sardi-hibiscus
- sardi-mono
- sardi-niagara
- sardi-orchid
- sardi-purple
- sardi-tacao
- sardi-tory

### Theme Features

Each theme provides:

- **Standard icons** for all actions (shutdown, restart, suspend, hibernate, lock, logout, cancel)
- **Blur variants** for hover effects - icons display with a blur effect when you hover over them
- **CSS styling** for label colors and text appearance
- **SVG-based graphics** for crisp scaling at any size

The theme system is extensible - you can create custom themes by creating a new directory in `/usr/share/archlinux-logout-themes/themes/` with appropriately named SVG files and a `theme.css` file.

## Session Support

The application supports:
- **X11 Sessions**: Full mouse position detection for multi-monitor setups
- **Wayland Sessions**: Graceful fallback to primary monitor display
- **Multiple Desktop Environments**: Includes logout commands for 50+ DEs and window managers (GNOME, KDE, Xfce, i3, Hyprland, and many more)

## Installation

### From Package Manager

```bash
pacman -S archlinux-logout
```

### From Source

Clone the repository and follow the build instructions in the PKGBUILD file.

## Development

### Project Structure

```text
archlinux-logout/
├── usr/share/archlinux-logout/
│   ├── archlinux-logout.py       # Main application entry point
│   ├── GUI.py                    # GTK4 UI components
│   ├── Functions.py              # Utility functions and config handling
│   └── ...
├── usr/share/archlinux-logout-themes/
│   └── themes/                   # Theme directories
└── etc/archlinux-logout.conf     # Default system configuration
```

### Running from Source

```bash
python3 usr/share/archlinux-logout/archlinux-logout.py
```

## Troubleshooting

### Config File Corruption

If the configuration file becomes corrupted, it will be automatically detected and reset to defaults.

### Permission Issues

The application requires appropriate permissions to execute power management commands. On systems using systemd, ensure your user is in the appropriate groups:

```bash
sudo usermod -aG wheel $USER
```

### Monitor Detection

If the logout menu appears on the wrong monitor:
- Ensure `xdotool` is installed for X11 session support
- On Wayland, the menu will always appear on the primary monitor

## Learning Resources

For more information about the tool and setup guides, visit our video playlist:

📺 **[ArchLinux Logout Video Tutorials](https://www.youtube.com/playlist?list=PLlloYVGq5pS7KfhUhcQaUAGV28kmA2OSt)** - 21+ comprehensive videos covering installation, configuration, theming, and customization

## Authors

- Brad Heffernan
- Fennec
- Erik Dubois

<!-- KIRO-FUNDING-FOOTER:START — managed by Kiro-HQ/cascade-readme-footer.sh -->
## Help fund Kiro

Everything I build here stays free and open — always. If Kiro or any of these
tools have ever saved you time or taught you something, a small monthly
contribution helps keep the work going. Donations target break-even, nothing
more — the core always stays free for everyone.

- GitHub Sponsors: https://github.com/sponsors/erikdubois
- Patreon: https://www.patreon.com/c/kiroproject
- YouTube memberships: https://www.youtube.com/@ErikDubois/join
- Ko-fi: https://ko-fi.com/erikdubois
- PayPal: https://www.paypal.me/erikdubois
<!-- KIRO-FUNDING-FOOTER:END -->

## License

See LICENSE file in the repository for details.
