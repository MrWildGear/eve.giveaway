# 🎮 EVE Online Giveaway Tool

A real-time giveaway and game management tool for EVE Online fleet operations. Automatically monitors EVE chat logs and manages interactive games with participants.

## ✨ Features

- **Real-time Chat Monitoring** - Automatically detects commands and entries from EVE chat logs
- **Multiple Game Types** - Price is Right and Guess the Number games
- **Automatic Timer** - Games automatically end after 2 minutes
- **Multiple Winner Support** - Handles ties and split prizes
- **Dark Mode GUI** - Modern, easy-to-read interface
- **Sortable Participants** - Click column headers to sort A-Z or Z-A
- **Collapsible Sections** - Hide instructions when not needed
- **Window Persistence** - Remembers window size and position
- **Case Insensitive Commands** - Commands work regardless of capitalization
- **🌍 Universal Compatibility** - Works on any computer with EVE Online installed
- **🔍 Smart Path Detection** - Automatically finds EVE logs on any system
- **👑 Flexible Admin System** - Works with any admin usernames configured

## 🎯 Game Types

### 🏆 Price is Right (PIR)
- **Objective**: Get the closest guess **without going over** the target number
- **Winner Selection**: 
  - Only guesses ≤ target are valid
  - Highest valid guess wins
  - Multiple players with same guess split the prize
- **Command**: `!PIR min-max` (e.g., `!PIR 1-100`)

### 🎲 Guess the Number (GTN)
- **Objective**: Get the **exact target number**
- **Winner Selection**: Only exact matches win
- **Command**: `!GTN min-max` (e.g., `!GTN 1-1000`)

## 🎮 Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!PIR min-max` | Start Price is Right game | `!PIR 0-1000` |
| `!GTN min-max` | Start Guess the Number game | `!GTN 1-500` |
| `!stop` | End current game and select winner | `!stop` |
| `!status` | Show game status and time remaining | `!status` |
| `!clear` | Clear current game | `!clear` |

**Note**: All commands are case-insensitive (`!pir`, `!PIR`, `!Pir` all work)

## 🎯 Player Commands

| Command | Description | Example |
|---------|-------------|---------|
| `?number` | Enter current game with number | `?500` |
| `? number` | Enter with space (also works) | `? 500` |

## 📁 Project Structure

```
eve.giveaway/
├── src/                    # Source code
│   └── main.py            # Main application
├── build/                  # Build and distribution scripts
│   ├── build_exe.bat      # Windows build script
│   ├── build_exe.ps1      # PowerShell build script
│   ├── EVE_Giveaway_Tool.spec  # PyInstaller configuration
│   └── create_share_folder.bat # Sharing utility
├── docs/                   # Documentation
│   ├── BUILD_SECURITY.md  # Security build guide
│   └── COMPATIBILITY_GUIDE.md # Cross-platform compatibility
├── templates/              # Configuration templates
│   └── admins.template.txt # Admin users template
├── admins.txt              # Your admin users (edit this)
├── config.txt              # Your configuration (edit this)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- EVE Online installed with chat logging enabled

### Quick Start
1. **Clone/Download** the project files
2. **Automatic Setup** (Recommended):
   - Double-click `setup.bat` for complete installation
   - Or double-click `install.bat` for basic installation
3. **Manual Setup**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Tool**:
   ```bash
   python src\main.py
   ```
   Or double-click `run.bat` on Windows

### EVE Chat Log Setup
The tool **automatically detects** your EVE Online logs location:
- **Standard**: `~/Documents/EVE/logs/Chatlogs/`
- **Alternative**: `~/Documents/EVE/logs/Gamelogs/`
- **Custom**: Configure in settings if needed
- **Multi-Platform**: Works on Windows, macOS, and Linux
- **Smart Detection**: Finds logs even in non-standard locations

### Building Standalone Executable
To create a standalone `.exe` file that doesn't require Python:

1. **Run the build script**:
   ```bash
   # Double-click build/build_exe.bat
   # Or run: python -m PyInstaller --onefile --windowed src\main.py
   ```

2. **Find your executable**:
   - Located in the `dist/` folder
   - File: `EVE_Giveaway_Tool.exe`

3. **Benefits**:
   - No Python installation required
   - Portable - copy to any Windows computer
   - Professional standalone application
   - Easy distribution to other users

## 🎮 How to Play

### Starting a Game
1. **Admin** types: `!PIR 1-100` or `!GTN 1-1000`
2. **Tool generates** a random target number within the range
3. **Game starts** with 2-minute countdown timer

### Players Enter
- **Players type**: `?50`, `?100`, etc.
- **Tool validates** guesses are within range
- **Participants list** updates in real-time
- **Duplicate entries** are prevented

### Game Ends
- **Automatic**: After 2 minutes
- **Manual**: Admin types `!stop`
- **Winner selected** based on game rules
- **Results displayed** in Game Status

## 🖥️ GUI Features

### 🎯 Game Status Section
- Real-time game information
- Countdown timer with color coding
- Game results and winner announcements

### 👥 Participants Section
- Sortable columns (Username, Guess, Time)
- Click headers to sort A-Z or Z-A
- Real-time updates as players enter

### 📖 How to Use Section
- Collapsible instructions
- Copyable text content
- Complete command reference

### 🎨 Dark Mode
- Dark background with white text
- Professional gaming aesthetic
- Easy on the eyes during long sessions

## 🔧 Configuration

### Admin Users
1. **Copy the template**: `copy admins.template.txt admins.txt`
2. **Edit the file**: Replace usernames with your actual admin users
3. **Format**: One username per line, `#` for comments
4. **Universal**: Works with any character names from any EVE server
5. **Flexible**: Supports special characters and spaces in usernames

```txt
<<<<<<< HEAD
# Example admins.txt content:
YourUsername
=======
# Add one username per line
YourOtherAdminName
>>>>>>> 397e309ac4f64f9b6491de52ddfdf7e26a528ede
Fleet Commander
Corporation Leader
```

**Note**: Lines starting with `#` are comments and ignored. Empty lines are also ignored.

### Game Duration
Currently set to 2 minutes. To change, modify:
```python
'end_time': datetime.now() + timedelta(minutes=2)
```

## 📁 Project Structure

```
eve.giveaway/
├── src/                 # Source code folder
│   ├── main.py         # Main application
│   └── admins.template.txt  # Admin configuration template
├── requirements.txt     # Python dependencies
├── admins.template.txt  # Admin configuration template
├── setup.bat           # Complete setup installer (recommended)
├── install.bat         # Basic dependency installer
├── run.bat             # Windows launcher
├── build_exe.bat       # Build standalone executable
├── build_exe.ps1       # PowerShell build script (recommended)
├── BUILD_SECURITY.md   # Build security guide
├── COMPATIBILITY_GUIDE.md  # Cross-platform compatibility guide
├── diagnose.bat        # System diagnostics tool
└── README.md           # This file
```

## 🐛 Troubleshooting

### White Screen / GUI Not Loading
If you see a white screen or the application doesn't load properly:

1. **Run the diagnostic tool**:
   - Double-click `diagnose.bat` to check your system
   - This will test Python, tkinter, and basic GUI functionality

2. **Test basic GUI**:
   - Run `python src\main.py` to test the main application
   - If this works, the executable should work too

3. **Common causes**:
   - **Missing tkinter**: Python installed without GUI support
   - **Display drivers**: Outdated or incompatible graphics drivers
   - **Windows theme**: Dark/light mode conflicts
   - **Python version**: Incompatible Python installation

4. **Solutions**:
   - Reinstall Python with "Add to PATH" and "tcl/tk and IDLE" options
   - Update graphics drivers
   - Try running as administrator
   - Check Windows display scaling settings

### Chat Not Detected
- Verify EVE Online is saving chat logs
- Check the logs directory exists
- Ensure the tool has read permissions

### Commands Not Working
- Verify you're in the admin list
- Check command format (e.g., `!PIR 1-100`)
- Ensure game is active

### GUI Issues
- Try resizing the window
- Check if window settings file is corrupted
- Restart the application

## 🌍 Compatibility

### **Universal Compatibility**
✅ **Works on any computer** with EVE Online installed  
✅ **Any admin configuration** - supports any usernames  
✅ **Automatic path detection** - finds EVE logs automatically  
✅ **Cross-platform support** - Windows, macOS, Linux  
✅ **Portable installation** - works from any directory  

### **Smart Detection Features**
- 🔍 **EVE Logs**: Automatically finds chat logs on any system
- 👑 **Admin Files**: Searches multiple locations for `admins.txt`
- 📝 **File Encodings**: Handles UTF-16, UTF-8, CP1252, and more
- 🎮 **EVE Versions**: Compatible with any EVE Online installation

### **System Requirements**
- **Operating System**: Windows 7+, macOS 10.12+, Linux (Ubuntu 16.04+)
- **Python**: 3.7+ (for development) or standalone executable
- **EVE Online**: Any version with chat logging enabled
- **Storage**: 50MB free space
- **Memory**: 100MB RAM minimum

## 📝 Requirements

```
tkinter          # GUI framework (included with Python)
watchdog         # File system monitoring
```

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the tool!

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Gaming!** 🎮✨
