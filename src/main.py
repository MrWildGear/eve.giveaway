import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
import random
import time
import sys
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import json
import configparser

class ConfigManager:
    """Manages application configuration from config.txt file"""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.txt'
        self.load_config()
    
    def load_config(self):
        """Load configuration from config.txt file"""
        try:
            if os.path.exists(self.config_file):
                # Read as regular text file since it's not standard INI format
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Parse the custom format
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'EVE_LOGS_PATH':
                            self.eve_logs_path = value if value else None
                        elif key == 'GAME_TIMER_MINUTES':
                            try:
                                self.game_timer_minutes = int(value)
                            except ValueError:
                                self.game_timer_minutes = 2
                        elif key == 'DEBUG_MODE':
                            self.debug_mode = value.lower() == 'true'
                        else:
                            # Store other config values
                            if not hasattr(self, 'other_config'):
                                self.other_config = {}
                            self.other_config[key] = value
            else:
                # Default values if no config file
                self.eve_logs_path = None
                self.game_timer_minutes = 2
                self.debug_mode = False
                
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            # Fallback to defaults
            self.eve_logs_path = None
            self.game_timer_minutes = 2
            self.debug_mode = False
    
    def get_eve_logs_path(self):
        """Get the configured EVE logs path or None for auto-detection"""
        return self.eve_logs_path
    
    def get_game_timer_minutes(self):
        """Get the configured game timer duration in minutes"""
        return self.game_timer_minutes
    
    def is_debug_mode(self):
        """Check if debug mode is enabled"""
        return self.debug_mode

class EVEChatMonitor(FileSystemEventHandler):
    def __init__(self, game_manager, eve_logs_path=None):
        self.game_manager = game_manager
        if eve_logs_path:
            self.eve_logs_path = eve_logs_path
        else:
            self.eve_logs_path = self.detect_eve_logs_path()
        self.current_files = {}
        
    def detect_eve_logs_path(self):
        """Detect EVE logs path across different operating systems and configurations"""
        possible_paths = []
        
        # Windows paths
        if os.name == 'nt':
            # Standard Windows paths
            possible_paths.extend([
                os.path.expanduser("~/Documents/EVE/logs/Chatlogs"),
                os.path.expanduser("~/Documents/EVE/logs/Gamelogs"),  # Some EVE versions use this
                os.path.expanduser("~/My Documents/EVE/logs/Chatlogs"),  # Non-English Windows
                os.path.expanduser("~/My Documents/EVE/logs/Gamelogs"),
                os.path.expanduser("~/OneDrive/Documents/EVE/logs/Chatlogs"),  # OneDrive
                os.path.expanduser("~/OneDrive/Documents/EVE/logs/Gamelogs"),
            ])
            
            # Check common drive letters
            for drive in ['C:', 'D:', 'E:']:
                possible_paths.extend([
                    f"{drive}/Users/{os.getenv('USERNAME', '')}/Documents/EVE/logs/Chatlogs",
                    f"{drive}/Users/{os.getenv('USERNAME', '')}/Documents/EVE/logs/Gamelogs",
                    f"{drive}/Users/{os.getenv('USERNAME', '')}/My Documents/EVE/logs/Chatlogs",
                    f"{drive}/Users/{os.getenv('USERNAME', '')}/My Documents/EVE/logs/Gamelogs",
                ])
        
        # macOS paths
        elif os.name == 'posix' and os.uname().sysname == 'Darwin':
            possible_paths.extend([
                os.path.expanduser("~/Documents/EVE/logs/Chatlogs"),
                os.path.expanduser("~/Documents/EVE/logs/Gamelogs"),
            ])
        
        # Linux paths
        elif os.name == 'posix':
            possible_paths.extend([
                os.path.expanduser("~/Documents/EVE/logs/Chatlogs"),
                os.path.expanduser("~/Documents/EVE/logs/Gamelogs"),
                os.path.expanduser("~/EVE/logs/Chatlogs"),
                os.path.expanduser("~/EVE/logs/Gamelogs"),
            ])
        
        # Test each path and return the first valid one
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                print(f"DEBUG: Found EVE logs directory: {path}")
                return path
        
        # If no path found, return the most likely default
        default_path = os.path.expanduser("~/Documents/EVE/logs/Chatlogs")
        print(f"WARNING: No EVE logs directory found. Using default: {default_path}")
        return default_path
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f"DEBUG: File modified: {event.src_path}")
            # Minimal delay to ensure file is fully written
            time.sleep(0.05)
            self.process_chat_log(event.src_path)
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f"DEBUG: New file created: {event.src_path}")
            # Minimal delay to ensure file is fully written
            time.sleep(0.1)
            self.process_chat_log(event.src_path)
    
    def process_chat_log(self, file_path):
        try:
            # Enhanced encoding detection for EVE Online logs
            encodings = ['utf-16', 'utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1', 'latin-1']
            lines = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        lines = f.readlines()
                        used_encoding = encoding
                        break
                except Exception as e:
                    continue
            
            if lines:
                # Process the last line (newest message)
                last_line = lines[-1].strip()
                if last_line:  # Only process non-empty lines
                    # Clean up EVE log format: remove null bytes and fix spacing
                    cleaned_line = self.clean_eve_log_line(last_line)
                    if cleaned_line:
                        print(f"DEBUG: Read with encoding: {used_encoding}")
                        print(f"DEBUG: Original line: '{last_line[:100]}...'")
                        print(f"DEBUG: Cleaned line: '{cleaned_line}'")
                        self.parse_message(cleaned_line)
                        
                        # Check if we should switch to a more recent chat log file
                        self.check_for_newer_chatlog()
        except Exception as e:
            print(f"Error reading chat log {file_path}: {e}")
            # Try to provide more helpful error information
            try:
                file_size = os.path.getsize(file_path)
                print(f"File size: {file_size} bytes")
            except:
                pass
    
    def check_for_newer_chatlog(self):
        """Check if there's a newer chat log file and switch to it"""
        try:
            if not hasattr(self, 'eve_logs_path') or not self.eve_logs_path:
                return
                
            # Find all chat log files in the directory
            chat_files = []
            for filename in os.listdir(self.eve_logs_path):
                if filename.endswith('.txt') and 'Chat' in filename:
                    file_path = os.path.join(self.eve_logs_path, filename)
                    try:
                        mod_time = os.path.getmtime(file_path)
                        chat_files.append((filename, mod_time, file_path))
                    except:
                        continue
            
            if not chat_files:
                return
                
            # Sort by modification time (newest first)
            chat_files.sort(key=lambda x: x[1], reverse=True)
            newest_file = chat_files[0]
            
            # Check if the newest file is different from what we're currently monitoring
            current_file = getattr(self, 'current_chat_file', None)
            if current_file != newest_file[0]:
                print(f"DEBUG: Newer chat log detected: {newest_file[0]} (was monitoring: {current_file})")
                self.current_chat_file = newest_file[0]
                
                # Process the newest file to catch up on any missed messages
                print(f"DEBUG: Processing newest chat log: {newest_file[0]}")
                self.process_chat_log(newest_file[2])
                
        except Exception as e:
            print(f"Error checking for newer chat log: {e}")
    
    def clean_eve_log_line(self, line):
        """Clean up EVE log line by removing null bytes and fixing spacing"""
        try:
            # Remove null bytes completely
            cleaned = line.replace('\x00', '')
            
            # If the line contains the expected pattern, clean it up
            if '[' in cleaned and ']' in cleaned and '>' in cleaned:
                # Extract the timestamp part and clean it
                start_bracket = cleaned.find('[')
                end_bracket = cleaned.find(']')
                
                if start_bracket != -1 and end_bracket != -1:
                    # Get the timestamp content (without brackets)
                    timestamp_content = cleaned[start_bracket+1:end_bracket].strip()
                    
                    # Clean the timestamp content - remove excessive spaces but preserve date/time structure
                    timestamp_content = re.sub(r'\s+', ' ', timestamp_content)
                    
                    # Reconstruct with proper spacing: [ timestamp ]
                    timestamp_section = f"[ {timestamp_content} ]"
                    
                    # Clean the rest of the line - remove excessive spaces but preserve structure
                    rest_of_line = cleaned[end_bracket+1:].strip()
                    # Remove excessive spaces but keep single spaces around >
                    rest_of_line = re.sub(r'\s+', ' ', rest_of_line)
                    
                    # Reconstruct the cleaned line
                    cleaned_line = timestamp_section + ' ' + rest_of_line
                    return cleaned_line
            
            return cleaned
        except Exception as e:
            print(f"Error cleaning EVE log line: {e}")
            return line
    
    def parse_message(self, message):
        # Enhanced EVE chat format parsing for different log formats
        patterns = [
            # Standard format: [ timestamp ] CharacterName > message
            r'\[ ([\d\.]+ [\d:]+) \] ([^>]+) > (.+)',
            # Alternative format: [ timestamp ] CharacterName: message
            r'\[ ([\d\.]+ [\d:]+) \] ([^:]+): (.+)',
            # Compact format: [timestamp] CharacterName > message
            r'\[([\d\.]+ [\d:]+)\] ([^>]+) > (.+)',
            # Minimal format: CharacterName > message
            r'([^>]+) > (.+)',
            # EVE specific format: [timestamp] CharacterName > message
            r'\[([\d\.]+ [\d:]+)\] ([^>]+) > (.+)',
        ]
        
        match = None
        used_pattern = None
        
        for pattern in patterns:
            match = re.match(pattern, message)
            if match:
                used_pattern = pattern
                break
        
        if match:
            if len(match.groups()) == 3:
                # Pattern with timestamp
                timestamp, character_name, content = match.groups()
                print(f"DEBUG: Used pattern: {used_pattern}")
            elif len(match.groups()) == 2:
                # Pattern without timestamp
                character_name, content = match.groups()
                timestamp = "unknown"
                print(f"DEBUG: Used pattern (no timestamp): {used_pattern}")
            else:
                print(f"DEBUG: Unexpected number of groups: {len(match.groups())}")
                return
            
            character_name = character_name.strip()
            content = content.strip()
            
            print(f"DEBUG: Parsed message - Timestamp: '{timestamp}', Character: '{character_name}', Content: '{content}'")
            
            # Check for admin commands (start with !) - case insensitive
            if content.lower().startswith('!pir '):
                print(f"DEBUG: Detected PIR command from {character_name}")
                self.game_manager.start_pir_game(character_name, content)
            elif content.lower().startswith('!gtn '):
                print(f"DEBUG: Detected GTN command from {character_name}")
                self.game_manager.start_gtn_game(character_name, content)
            elif content.lower().startswith('!stop'):
                print(f"DEBUG: Detected stop command from {character_name}")
                self.game_manager.stop_game(character_name)
            elif content.lower().startswith('!status'):
                print(f"DEBUG: Detected status command from {character_name}")
                self.game_manager.show_status(character_name)
            elif content.lower().startswith('!clear'):
                print(f"DEBUG: Detected clear command from {character_name}")
                self.game_manager.clear_game(character_name)
            # Check for player entries (start with ?)
            elif content.startswith('?'):
                print(f"DEBUG: Detected player entry from {character_name}: {content}")
                self.game_manager.enter_game(character_name, content)
            else:
                print(f"DEBUG: No command detected in content: '{content}'")
        else:
            print(f"DEBUG: Message did not match any pattern: '{message}'")
            # Try to extract any potential command from the message
            if '!' in message:
                print(f"DEBUG: Found '!' in message, might be a command: {message}")

class GameManager:
    def __init__(self, gui, config_manager=None):
        self.gui = gui
        self.config_manager = config_manager
        self.current_game = None
        self.participants = {}
        self.admin_users = set()  # Add admin usernames here
        
    def start_pir_game(self, admin_name, command):
        print(f"DEBUG: PIR game command from {admin_name}, checking admin status...")
        if not self.is_admin(admin_name):
            print(f"DEBUG: {admin_name} is NOT an admin, command rejected")
            return
        print(f"DEBUG: {admin_name} is confirmed admin, starting PIR game")
            
        try:
            # Handle case-insensitive command parsing using regex
            import re
            # More strict pattern: exactly two numbers separated by single dash, no extra characters
            range_match = re.search(r'!pir\s+(\d+)-(\d+)(?:\s|$)', command, re.IGNORECASE)
            if range_match:
                min_val, max_val = map(int, range_match.groups())
                # Validate range
                if min_val > max_val:
                    self.gui.update_game_status(f"❌ Invalid range: {min_val}-{max_val}. Min must be ≤ Max.")
                    return
                target = random.randint(min_val, max_val)
                
                self.current_game = {
                    'type': 'PIR',
                    'admin': admin_name,
                    'range': f"{min_val}-{max_val}",
                    'target': target,
                    'start_time': datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=self.config_manager.get_game_timer_minutes()),
                    'participants': {},
                    'active': True
                }
                
                self.gui.update_game_status(f"🎯 Price is Right game started by {admin_name}!\nRange: {min_val}-{max_val}\n⏰ Game ends in {self.config_manager.get_game_timer_minutes()} minutes!\nPlayers use ?number to enter!")
                self.gui.clear_participants()
                
                # Start the game timer
                self.start_game_timer()
                
        except Exception as e:
            print(f"Error starting PIR game: {e}")
    
    def start_gtn_game(self, admin_name, command):
        print(f"DEBUG: GTN game command from {admin_name}, checking admin status...")
        if not self.is_admin(admin_name):
            print(f"DEBUG: {admin_name} is NOT an admin, command rejected")
            return
        print(f"DEBUG: {admin_name} is confirmed admin, starting GTN game")
            
        try:
            # Handle case-insensitive command parsing using regex
            import re
            # More strict pattern: exactly two numbers separated by single dash, no extra characters
            range_match = re.search(r'!gtn\s+(\d+)-(\d+)(?:\s|$)', command, re.IGNORECASE)
            if range_match:
                min_val, max_val = map(int, range_match.groups())
                # Validate range
                if min_val > max_val:
                    self.gui.update_game_status(f"❌ Invalid range: {min_val}-{max_val}. Min must be ≤ Max.")
                    return
                target = random.randint(min_val, max_val)
                
                self.current_game = {
                    'type': 'GTN',
                    'admin': admin_name,
                    'range': f"{min_val}-{max_val}",
                    'target': target,
                    'start_time': datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=self.config_manager.get_game_timer_minutes()),
                    'participants': {},
                    'active': True
                }
                
                self.gui.update_game_status(f"🎲 Guess the Number game started by {admin_name}!\nRange: {min_val}-{max_val}\n⏰ Game ends in {self.config_manager.get_game_timer_minutes()} minutes!\nPlayers use ?number to enter!")
                self.gui.clear_participants()
                
                # Start the game timer
                self.start_game_timer()
                
        except Exception as e:
            print(f"Error starting GTN game: {e}")
    
    def enter_game(self, character_name, command):
        if not self.current_game or not self.current_game['active']:
            print(f"DEBUG: No active game or game not active for {character_name}")
            return
            
        try:
            # Extract number after ? (e.g., ?500 -> 500)
            # Handle both ?500 and ? 500 (with space)
            if command.startswith('?'):
                guess_str = command[1:].strip()  # Remove the ? and trim
                print(f"DEBUG: Extracted guess string: '{guess_str}' from command: '{command}'")
                
                # Try to parse the number
                try:
                    guess = int(guess_str)
                    print(f"DEBUG: Parsed guess number: {guess}")
                except ValueError:
                    # If that fails, try to find any number in the string
                    import re
                    number_match = re.search(r'\d+', guess_str)
                    if number_match:
                        guess = int(number_match.group())
                        print(f"DEBUG: Found number in string: {guess}")
                    else:
                        raise ValueError(f"No valid number found in: {command}")
                
                min_val, max_val = map(int, self.current_game['range'].split('-'))
                
                if min_val <= guess <= max_val:
                    # Check if player already entered
                    if character_name in self.current_game['participants']:
                        print(f"DEBUG: {character_name} already entered with {self.current_game['participants'][character_name]['guess']}")
                        self.gui.update_game_status(f"⚠️ {character_name} already entered with {self.current_game['participants'][character_name]['guess']}")
                        return
                    
                    print(f"DEBUG: Adding {character_name} with guess {guess}")
                    self.current_game['participants'][character_name] = {
                        'guess': guess,
                        'time': datetime.now()
                    }
                    
                    print(f"DEBUG: Calling GUI add_participant for {character_name}")
                    self.gui.add_participant(character_name, guess)
                    self.gui.update_game_status(f"✅ {character_name} entered with {guess}!")
                else:
                    print(f"DEBUG: Guess {guess} outside range {min_val}-{max_val}")
                    self.gui.update_game_status(f"❌ {character_name}'s guess {guess} is outside the range {min_val}-{max_val}")
            else:
                print(f"DEBUG: Command doesn't start with ?: {command}")
                self.gui.update_game_status(f"❌ Invalid format from {character_name}. Use ?number (e.g., ?500)")
                
        except ValueError as e:
            print(f"DEBUG: Invalid number format from {character_name}: {command} - Error: {e}")
            self.gui.update_game_status(f"❌ Invalid number format from {character_name}. Use ?number (e.g., ?500)")
        except Exception as e:
            print(f"Error processing entry: {e}")
    
    def stop_game(self, admin_name):
        print(f"DEBUG: Stop game command from {admin_name}, checking admin status...")
        if not self.is_admin(admin_name):
            print(f"DEBUG: {admin_name} is NOT an admin, command rejected")
            return
        if not self.current_game:
            print(f"DEBUG: No active game to stop")
            return
        print(f"DEBUG: {admin_name} is confirmed admin, stopping game")
            
        print(f"DEBUG: Stopping game. Type: {self.current_game['type']}, Target: {self.current_game['target']}")
        print(f"DEBUG: Participants: {self.current_game['participants']}")
        
        if self.current_game['type'] == 'PIR':
            winner = self.select_pir_winner()
            print(f"DEBUG: PIR winner selected: {winner}")
        else:  # GTN
            winner = self.select_gtn_winner()
            print(f"DEBUG: GTN winner selected: {winner}")
        
        if winner:
            if winner['type'] == 'single':
                self.gui.update_game_status(f"🏆 Game ended! Winner: {winner['name']} with guess {winner['guess']}\n🎯 Target was: {self.current_game['target']}")
            else:  # multiple winners
                winner_names = ", ".join(winner['names'])
                self.gui.update_game_status(f"🏆 Game ended! Winners: {winner_names} with guess {winner['guess']}\n🎯 Target was: {self.current_game['target']}")
        else:
            self.gui.update_game_status("❌ Game ended! No participants.")
        
        # Stop timer thread and clean up
        self._cleanup_timer_thread()
        self.current_game['active'] = False
    
    def clear_game(self, admin_name):
        print(f"DEBUG: Clear game command from {admin_name}, checking admin status...")
        if not self.is_admin(admin_name):
            print(f"DEBUG: {admin_name} is NOT an admin, command rejected")
            return
        print(f"DEBUG: {admin_name} is confirmed admin, clearing game")
            
        # Stop timer thread and clean up
        self._cleanup_timer_thread()
        self.current_game = None
        self.gui.clear_participants()
        self.gui.update_game_status("🧹 Game cleared! Ready for new game.")
    
    def select_pir_winner(self):
        if not self.current_game['participants']:
            print("DEBUG: No participants in game")
            return None
            
        print(f"DEBUG: Selecting PIR winner. Target: {self.current_game['target']}")
        print(f"DEBUG: All participants: {self.current_game['participants']}")
        
        # Price is Right: closest without going over
        valid_guesses = {name: data for name, data in self.current_game['participants'].items() 
                        if data['guess'] <= self.current_game['target']}
        
        print(f"DEBUG: Valid guesses (≤ target): {valid_guesses}")
        
        if not valid_guesses:
            print("DEBUG: No valid guesses found")
            return None
            
        # Find the highest valid guess (closest without going over)
        max_guess = max(valid_guesses.values(), key=lambda x: x['guess'])['guess']
        
        # Find ALL players with this winning guess
        winners = [name for name, data in valid_guesses.items() 
                  if data['guess'] == max_guess]
        
        print(f"DEBUG: Winners found: {winners} with guess {max_guess}")
        
        if len(winners) == 1:
            # Single winner
            return {
                'name': winners[0],
                'guess': max_guess,
                'type': 'single'
            }
        else:
            # Multiple winners - return list
            return {
                'names': winners,
                'guess': max_guess,
                'type': 'multiple'
            }
    
    def select_gtn_winner(self):
        if not self.current_game['participants']:
            return None
            
        # Guess the Number: exact match
        exact_matches = {name: data for name, data in self.current_game['participants'].items() 
                        if data['guess'] == self.current_game['target']}
        
        if exact_matches:
            if len(exact_matches) == 1:
                # Single winner
                winner_name = list(exact_matches.keys())[0]
                return {
                    'name': winner_name,
                    'guess': exact_matches[winner_name]['guess'],
                    'type': 'single'
                }
            else:
                # Multiple winners - return list
                winner_names = list(exact_matches.keys())
                winner_guess = list(exact_matches.values())[0]['guess']
                return {
                    'names': winner_names,
                    'guess': winner_guess,
                    'type': 'multiple'
                }
        
        return None
    
    def show_status(self, admin_name):
        print(f"DEBUG: Status command from {admin_name}, checking admin status...")
        if not self.is_admin(admin_name):
            print(f"DEBUG: {admin_name} is NOT an admin, command rejected")
            return
        print(f"DEBUG: {admin_name} is confirmed admin, showing status")
            
        if not self.current_game:
            self.gui.update_game_status("📊 No active game. Use !PIR or !GTN to start one!")
            return
            
        # Calculate time remaining
        time_remaining = self.current_game['end_time'] - datetime.now()
        if time_remaining.total_seconds() > 0:
            minutes = int(time_remaining.total_seconds() // 60)
            seconds = int(time_remaining.total_seconds() % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
        else:
            time_str = "00:00"
            
        status = f"📊 Current game: {self.current_game['type']}\n"
        status += f"🎯 Range: {self.current_game['range']}\n"
        status += f"👥 Participants: {len(self.current_game['participants'])}\n"
        status += f"🟢 Active: {self.current_game['active']}\n"
        status += f"⏰ Started: {self.current_game['start_time'].strftime('%H:%M:%S')}\n"
        status += f"⏳ Time remaining: {time_str}"
        
        self.gui.update_game_status(status)
    
    def is_admin(self, username):
        """Check if username is in admin list by reading from admins.txt file"""
        try:
            admin_list = set()
            # Enhanced path detection for admins.txt
            possible_paths = [
                'admins.txt',  # Current working directory
                os.path.join(os.getcwd(), 'admins.txt'),  # Current working directory (explicit)
                os.path.join(os.path.dirname(__file__), 'admins.txt'),  # Same directory as script
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'admins.txt'),  # Parent directory
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'admins.txt'),  # Grandparent directory
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'admins.txt'),  # Great-grandparent directory
            ]
            
            # Add executable directory for PyInstaller builds
            if hasattr(sys, '_MEIPASS'):  # PyInstaller executable
                possible_paths.insert(0, os.path.join(sys._MEIPASS, 'admins.txt'))
                possible_paths.insert(0, os.path.join(os.path.dirname(sys.executable), 'admins.txt'))
            
            # Add user's home directory
            home_dir = os.path.expanduser("~")
            possible_paths.extend([
                os.path.join(home_dir, 'admins.txt'),
                os.path.join(home_dir, 'Documents', 'admins.txt'),
                os.path.join(home_dir, 'Desktop', 'admins.txt'),
            ])
            
            admin_file_found = False
            for admin_path in possible_paths:
                if os.path.exists(admin_path):
                    try:
                        # Try multiple encodings for better compatibility
                        encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
                        file_read = False
                        
                        for encoding in encodings:
                            try:
                                with open(admin_path, 'r', encoding=encoding) as f:
                                    for line in f:
                                        line = line.strip()
                                        # Skip empty lines and comments
                                        if line and not line.startswith('#'):
                                            admin_list.add(line)
                                    file_read = True
                                    break
                            except UnicodeDecodeError:
                                continue
                        
                        if file_read:
                            admin_file_found = True
                            print(f"DEBUG: Loaded admin list from: {admin_path}")
                            print(f"DEBUG: Admin users: {admin_list}")
                            break
                        else:
                            print(f"Warning: Could not read {admin_path} with any encoding")
                            
                    except Exception as e:
                        print(f"Warning: Could not read {admin_path}: {e}")
                        continue
            
            if not admin_file_found:
                # No admin file found - no admins will be available
                print("Warning: admins.txt not found in any location. No admin users will be available.")
                admin_list = set()
            
            return username in admin_list
        except Exception as e:
            print(f"Error reading admin list: {e}")
            # If there's an error reading the admin list, no admins will be available
            return False
    
    def start_game_timer(self):
        """Start a timer that will automatically end the game after configured minutes"""
        # Store reference to current timer thread for cleanup
        if hasattr(self, 'timer_thread') and self.timer_thread and self.timer_thread.is_alive():
            # Stop previous timer thread if it exists
            self.timer_thread.cancel = True
            self.timer_thread.join(timeout=1)
        
        def timer_thread():
            # Add cancel flag to thread
            timer_thread.cancel = False
            while self.current_game and self.current_game['active'] and not timer_thread.cancel:
                time.sleep(1)  # Check every second
                try:
                    if datetime.now() >= self.current_game['end_time']:
                        # Game time is up!
                        if self.current_game and self.current_game['active']:
                            self.current_game['active'] = False
                            self.gui.update_game_status("⏰ Time's up! Game ended automatically!")
                            
                            # Select winner
                            if self.current_game['type'] == 'PIR':
                                winner = self.select_pir_winner()
                            else:  # GTN
                                winner = self.select_gtn_winner()
                            
                            if winner:
                                if winner['type'] == 'single':
                                    self.gui.update_game_status(f"🏆 Game ended! Winner: {winner['name']} with guess {winner['guess']}\n🎯 Target was: {self.current_game['target']}")
                                else:  # multiple winners
                                    winner_names = ", ".join(winner['names'])
                                    self.gui.update_game_status(f"🏆 Game ended! Winners: {winner_names} with guess {winner['guess']}\n🎯 Target was: {self.current_game['target']}")
                            else:
                                self.gui.update_game_status("⏰ Game ended! No participants.")
                        break
                except Exception as e:
                    print(f"Error in timer thread: {e}")
                    break
        
        # Start timer in a separate thread
        self.timer_thread = threading.Thread(target=timer_thread, daemon=True)
        self.timer_thread.start()
    
    def _cleanup_timer_thread(self):
        """Clean up timer thread to prevent memory leaks and crashes"""
        if hasattr(self, 'timer_thread') and self.timer_thread and self.timer_thread.is_alive():
            try:
                self.timer_thread.cancel = True
                self.timer_thread.join(timeout=2)
                if self.timer_thread.is_alive():
                    print("Warning: Timer thread did not stop gracefully")
            except Exception as e:
                print(f"Error cleaning up timer thread: {e}")

class EVEGiveawayGUI:
    def __init__(self):
        try:
            self.root = tk.Tk()
            self.root.title("EVE Online Giveaway Tool")
            
            # Set a minimum window size to prevent layout issues
            self.root.minsize(800, 600)
            
            # Load saved window size and position
            self.load_window_settings()
            
            # Configuration manager
            self.config_manager = ConfigManager()
            
            # Game manager
            self.game_manager = GameManager(self, self.config_manager)
            
            # Chat monitor
            chat_monitor_path = self.config_manager.get_eve_logs_path()
            self.chat_monitor = EVEChatMonitor(self.game_manager, chat_monitor_path)
            self.observer = None
            
            # Setup GUI with error handling
            try:
                self.setup_gui()
            except Exception as e:
                print(f"Error setting up GUI: {e}")
                # Fallback to basic GUI if styling fails
                self.setup_basic_gui()
            
            self.start_monitoring()
            
            # Bind window close event to save settings
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Ensure the window is visible and focused
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            print(f"Critical error initializing GUI: {e}")
            # Show error message and exit gracefully
            if 'self.root' in locals():
                messagebox.showerror("Error", f"Failed to initialize GUI: {e}")
                self.root.destroy()
            else:
                print("Could not create root window")
            raise
    
    def setup_gui(self):
        # Apply dark mode styling
        self.apply_dark_mode()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # Game Status gets weight
        main_frame.rowconfigure(2, weight=1)  # Participants gets weight
        main_frame.rowconfigure(3, weight=0)  # Instructions doesn't need weight
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 EVE Online Giveaway Tool", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Game status
        status_frame = ttk.LabelFrame(main_frame, text="🎯 Game Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Add settings button to status frame
        status_header = ttk.Frame(status_frame)
        status_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        settings_btn = ttk.Button(status_header, text="⚙️ Settings", command=self.show_settings)
        settings_btn.grid(row=0, column=1, sticky=tk.E)
        
        # Status text below the header
        self.status_text = tk.Text(status_frame, height=6, width=90, font=("Consolas", 10), 
                                  bg="#2b2b2b", fg="white", insertbackground="white")
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Countdown timer display
        self.countdown_label = ttk.Label(status_frame, text="⏰ No active game", font=("Arial", 12, "bold"), foreground="white")
        self.countdown_label.grid(row=2, column=0, pady=(5, 0))
        
        # Participants
        participants_frame = ttk.LabelFrame(main_frame, text="👥 Participants", padding="10")
        participants_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for participants with sorting
        columns = ('Username', 'Guess', 'Time')
        self.participants_tree = ttk.Treeview(participants_frame, columns=columns, show='headings', height=12)
        
        # Store sort direction for each column
        self.sort_directions = {'Username': False, 'Guess': False, 'Time': False}
        
        for col in columns:
            self.participants_tree.heading(col, text=col, 
                                         command=lambda c=col: self.sort_column(c))
            self.participants_tree.column(col, width=200)
        
        self.participants_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for participants
        participants_scrollbar = ttk.Scrollbar(participants_frame, orient=tk.VERTICAL, command=self.participants_tree.yview)
        participants_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.participants_tree.configure(yscrollcommand=participants_scrollbar.set)
        
        # Instructions (collapsible)
        instructions_frame = ttk.LabelFrame(main_frame, text="📖 How to Use", padding="10")
        instructions_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Collapse/expand button for instructions
        self.instructions_collapsed = False
        instructions_toggle_btn = ttk.Button(instructions_frame, text="🔽 Hide", command=lambda: self.toggle_section("instructions"))
        instructions_toggle_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Instructions content frame
        self.instructions_content_frame = ttk.Frame(instructions_frame)
        self.instructions_content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        instructions = """🎮 ADMIN COMMANDS (use !) - Case Insensitive:
• !PIR min-max - Start Price is Right game (closest without going over)
  Example: !PIR 1-100, !pir 0-1000, !Pir 50-500
• !GTN min-max - Start Guess the Number game (exact match)
  Example: !GTN 1-100, !gtn 0-1000, !Gtn 50-500
• !stop - End current game and select winner
• !status - Show game status and time remaining
• !clear - Clear current game

🎯 PLAYER COMMANDS (use ?):
• ?number - Enter current game with number
  Example: ?50, ?100, ? 500 (space works too)

🏆 GAME RULES:
• Price is Right: Closest guess ≤ target wins
• Guess the Number: Exact match wins
• Multiple winners split prize if tied
• Games auto-end after 2 minutes
• Players can only enter once per game

⚙️ ADMIN SETUP:
• Edit admins.txt to add/remove admin users
• One username per line, # for comments

🔍 The tool automatically monitors EVE chat logs and updates in real-time."""
        
        # Make instructions copyable using Text widget
        self.instructions_text = tk.Text(self.instructions_content_frame, height=8, width=90, font=("Consolas", 10),
                                        bg="#2b2b2b", fg="white", insertbackground="white", wrap=tk.WORD)
        self.instructions_text.insert(tk.END, instructions)
        self.instructions_text.config(state=tk.DISABLED)  # Read-only but copyable
        self.instructions_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure frame weights
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=0)  # Countdown label doesn't need weight
        participants_frame.columnconfigure(0, weight=1)
        participants_frame.columnconfigure(1, weight=0)  # Scrollbar doesn't need weight
        participants_frame.rowconfigure(0, weight=1)
        instructions_frame.columnconfigure(0, weight=1)
        instructions_frame.rowconfigure(1, weight=1)  # Content frame gets the weight
        
    def setup_basic_gui(self):
        """Fallback GUI setup in case dark mode styling fails"""
        print("Applying basic GUI setup due to dark mode styling error.")
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # Game Status gets weight
        main_frame.rowconfigure(2, weight=1)  # Participants gets weight
        main_frame.rowconfigure(3, weight=0)  # Instructions doesn't need weight
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 EVE Online Giveaway Tool", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Game status
        status_frame = ttk.LabelFrame(main_frame, text="🎯 Game Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Add settings button to status frame
        status_header = ttk.Frame(status_frame)
        status_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        settings_btn = ttk.Button(status_header, text="⚙️ Settings", command=self.show_settings)
        settings_btn.grid(row=0, column=1, sticky=tk.E)
        
        # Status text below the header
        self.status_text = tk.Text(status_frame, height=6, width=90, font=("Consolas", 10), 
                                  bg="#2b2b2b", fg="white", insertbackground="white")
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Countdown timer display
        self.countdown_label = ttk.Label(status_frame, text="⏰ No active game", font=("Arial", 12, "bold"), foreground="white")
        self.countdown_label.grid(row=2, column=0, pady=(5, 0))
        
        # Participants
        participants_frame = ttk.LabelFrame(main_frame, text="👥 Participants", padding="10")
        participants_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for participants with sorting
        columns = ('Username', 'Guess', 'Time')
        self.participants_tree = ttk.Treeview(participants_frame, columns=columns, show='headings', height=12)
        
        # Store sort direction for each column
        self.sort_directions = {'Username': False, 'Guess': False, 'Time': False}
        
        for col in columns:
            self.participants_tree.heading(col, text=col, 
                                         command=lambda c=col: self.sort_column(c))
            self.participants_tree.column(col, width=200)
        
        self.participants_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for participants
        participants_scrollbar = ttk.Scrollbar(participants_frame, orient=tk.VERTICAL, command=self.participants_tree.yview)
        participants_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.participants_tree.configure(yscrollcommand=participants_scrollbar.set)
        
        # Instructions (collapsible)
        instructions_frame = ttk.LabelFrame(main_frame, text="📖 How to Use", padding="10")
        instructions_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Collapse/expand button for instructions
        self.instructions_collapsed = False
        instructions_toggle_btn = ttk.Button(instructions_frame, text="🔽 Hide", command=lambda: self.toggle_section("instructions"))
        instructions_toggle_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Instructions content frame
        self.instructions_content_frame = ttk.Frame(instructions_frame)
        self.instructions_content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        instructions = """🎮 ADMIN COMMANDS (use !) - Case Insensitive:
• !PIR min-max - Start Price is Right game (closest without going over)
  Example: !PIR 1-100, !pir 0-1000, !Pir 50-500
• !GTN min-max - Start Guess the Number game (exact match)
  Example: !GTN 1-100, !gtn 0-1000, !Gtn 50-500
• !stop - End current game and select winner
• !status - Show game status and time remaining
• !clear - Clear current game

🎯 PLAYER COMMANDS (use ?):
• ?number - Enter current game with number
  Example: ?50, ?100, ? 500 (space works too)

🏆 GAME RULES:
• Price is Right: Closest guess ≤ target wins
• Guess the Number: Exact match wins
• Multiple winners split prize if tied
• Games auto-end after 2 minutes
• Players can only enter once per game

⚙️ ADMIN SETUP:
• Edit admins.txt to add/remove admin users
• One username per line, # for comments

🔍 The tool automatically monitors EVE chat logs and updates in real-time."""
        
        # Make instructions copyable using Text widget
        self.instructions_text = tk.Text(self.instructions_content_frame, height=8, width=90, font=("Consolas", 10),
                                        bg="#2b2b2b", fg="white", insertbackground="white", wrap=tk.WORD)
        self.instructions_text.insert(tk.END, instructions)
        self.instructions_text.config(state=tk.DISABLED)  # Read-only but copyable
        self.instructions_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure frame weights
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=0)  # Countdown label doesn't need weight
        participants_frame.columnconfigure(0, weight=1)
        participants_frame.columnconfigure(1, weight=0)  # Scrollbar doesn't need weight
        participants_frame.rowconfigure(0, weight=1)
        instructions_frame.columnconfigure(0, weight=1)
        instructions_frame.rowconfigure(1, weight=1)  # Content frame gets the weight
    
    def start_monitoring(self):
        # Use configured path or enhanced auto-detection
        eve_logs_path = self.config_manager.get_eve_logs_path()
        if not eve_logs_path:
            # Use the enhanced path detection from EVEChatMonitor
            eve_logs_path = self.chat_monitor.detect_eve_logs_path()
        
        if os.path.exists(eve_logs_path):
            self.observer = Observer()
            self.observer.schedule(self.chat_monitor, eve_logs_path, recursive=False)
            self.observer.start()
            
            # Find and monitor the most recent chat log file
            self.find_and_monitor_latest_chatlog(eve_logs_path)
            
            # Process existing files in the directory
            self.process_existing_files(eve_logs_path)
            
            self.update_game_status(f"🔍 Monitoring EVE chat logs at: {eve_logs_path}\n✅ Ready for games!\n\nUse !PIR or !GTN to start a game!")
            
            # Start countdown timer update
            self.start_countdown_timer()
        else:
            # Try to find an alternative path
            alternative_path = self.chat_monitor.detect_eve_logs_path()
            if alternative_path != eve_logs_path and os.path.exists(alternative_path):
                self.observer = Observer()
                self.observer.schedule(self.chat_monitor, alternative_path, recursive=False)
                self.observer.start()
                
                # Find and monitor the most recent chat log file
                self.find_and_monitor_latest_chatlog(alternative_path)
                
                # Process existing files in the directory
                self.process_existing_files(alternative_path)
                
                self.update_game_status(f"🔍 Monitoring EVE chat logs at: {alternative_path}\n✅ Ready for games!\n\nUse !PIR or !GTN to start a game!")
                
                # Start countdown timer update
                self.start_countdown_timer()
            else:
                self.update_game_status(f"❌ EVE logs directory not found at: {eve_logs_path}\nAlternative path also not found: {alternative_path}\nPlease check your EVE Online installation or configure the path in settings.")
    
    def find_and_monitor_latest_chatlog(self, logs_directory):
        """Find the most recent chat log file and set it as the current one to monitor"""
        try:
            # Find all chat log files
            chat_files = []
            for filename in os.listdir(logs_directory):
                if filename.endswith('.txt') and 'Chat' in filename:
                    file_path = os.path.join(logs_directory, filename)
                    try:
                        mod_time = os.path.getmtime(file_path)
                        chat_files.append((filename, mod_time, file_path))
                    except:
                        continue
            
            if chat_files:
                # Sort by modification time (newest first)
                chat_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = chat_files[0]
                
                # Set this as the current chat file to monitor
                self.chat_monitor.current_chat_file = latest_file[0]
                print(f"DEBUG: Monitoring latest chat log: {latest_file[0]} (modified: {time.ctime(latest_file[1])})")
                
                # Process this file to catch up on any recent messages
                self.chat_monitor.process_chat_log(latest_file[2])
            else:
                print("DEBUG: No chat log files found in directory")
                
        except Exception as e:
            print(f"Error finding latest chat log: {e}")
    
    def restart_monitoring(self, new_path):
        """Restart file monitoring with a new path"""
        try:
            print(f"DEBUG: Restarting monitoring with new path: {new_path}")
            
            # Stop current monitoring
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            # Update chat monitor path
            self.chat_monitor.eve_logs_path = new_path
            
            # Start new monitoring
            if os.path.exists(new_path):
                self.observer = Observer()
                self.observer.schedule(self.chat_monitor, new_path, recursive=False)
                self.observer.start()
                
                # Process existing files in the new directory
                self.process_existing_files(new_path)
                
                self.update_game_status(f"🔄 Monitoring restarted at: {new_path}\n✅ Ready for games!")
                print(f"DEBUG: Monitoring restarted successfully at {new_path}")
            else:
                self.update_game_status(f"❌ Cannot monitor {new_path} - directory not found")
                print(f"DEBUG: Failed to restart monitoring - path not found: {new_path}")
                
        except Exception as e:
            print(f"Error restarting monitoring: {e}")
            self.update_game_status(f"❌ Error restarting monitoring: {e}")
    
    def process_existing_files(self, directory_path):
        """Process all existing .txt files in the directory"""
        try:
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return
            
            txt_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
            if not txt_files:
                print(f"DEBUG: No .txt files found in {directory_path}")
                return
            
            print(f"DEBUG: Processing {len(txt_files)} existing .txt files in {directory_path}")
            
            for filename in txt_files:
                file_path = os.path.join(directory_path, filename)
                try:
                    # Check if file has content (not empty)
                    if os.path.getsize(file_path) > 0:
                        print(f"DEBUG: Processing existing file: {filename}")
                        self.chat_monitor.process_chat_log(file_path)
                except Exception as e:
                    print(f"DEBUG: Error processing existing file {filename}: {e}")
                    
        except Exception as e:
            print(f"Error processing existing files: {e}")
    
    def start_countdown_timer(self):
        """Start a timer that updates the countdown display every second"""
        def countdown_update():
            while True:
                try:
                    if hasattr(self, 'game_manager') and self.game_manager.current_game and self.game_manager.current_game['active']:
                        # Calculate time remaining
                        time_remaining = self.game_manager.current_game['end_time'] - datetime.now()
                        if time_remaining.total_seconds() > 0:
                            minutes = int(time_remaining.total_seconds() // 60)
                            seconds = int(time_remaining.total_seconds() % 60)
                            time_str = f"⏰ Game ends in: {minutes:02d}:{seconds:02d}"
                            
                            # Color coding: red when less than 1 minute, orange when less than 2 minutes
                            if time_remaining.total_seconds() < 60:
                                self.countdown_label.config(foreground="#ff6b6b")  # Light red
                            elif time_remaining.total_seconds() < 120:
                                self.countdown_label.config(foreground="#ffa726")  # Light orange
                            else:
                                self.countdown_label.config(foreground="#66bb6a")  # Light green
                        else:
                            time_str = "⏰ Game ended!"
                            self.countdown_label.config(foreground="#9e9e9e")  # Light gray
                        
                        self.countdown_label.config(text=time_str)
                    else:
                        self.countdown_label.config(text="⏰ No active game", foreground="#9e9e9e")  # Light gray
                    
                    time.sleep(1)  # Update every second
                except Exception as e:
                    print(f"Error updating countdown: {e}")
                    time.sleep(1)
        
        # Start countdown in a separate thread
        countdown_thread = threading.Thread(target=countdown_update, daemon=True)
        countdown_thread.start()
        
        # Start chat log monitoring check every  seconds
        def chatlog_monitor():
            while True:
                try:
                    if hasattr(self, 'chat_monitor') and hasattr(self.chat_monitor, 'eve_logs_path'):
                        self.chat_monitor.check_for_newer_chatlog()
                    time.sleep(1)  # Check every 5 seconds
                except Exception as e:
                    print(f"Error in chat log monitor: {e}")
                    time.sleep(1)
        
        # Start chat log monitoring in a separate thread
        chatlog_thread = threading.Thread(target=chatlog_monitor, daemon=True)
        chatlog_thread.start()
    
    def show_settings(self):
        """Show settings dialog for configuring EVE logs path and other options"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("600x500")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Apply dark mode to settings window
        self.apply_dark_mode_to_window(settings_window)
        
        # Center the window
        settings_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(settings_window, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="⚙️ EVE Giveaway Tool Settings", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # EVE Logs Path
        path_frame = ttk.LabelFrame(main_frame, text="📁 EVE Chat Logs Path", padding="10")
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="Path to EVE Online chat logs folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.path_var = tk.StringVar(value=self.config_manager.get_eve_logs_path() or "")
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        browse_btn = ttk.Button(path_frame, text="Browse...", command=self.browse_eve_logs_path)
        browse_btn.grid(row=1, column=1, padx=(10, 0))
        
        ttk.Label(path_frame, text="Leave empty to use automatic detection", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W)
        
        # Game Timer
        timer_frame = ttk.LabelFrame(main_frame, text="⏰ Game Timer", padding="10")
        timer_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(timer_frame, text="Game duration in minutes:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.timer_var = tk.StringVar(value=str(self.config_manager.get_game_timer_minutes()))
        timer_entry = ttk.Entry(timer_frame, textvariable=self.timer_var, width=10)
        timer_entry.grid(row=1, column=0, sticky=tk.W)
        
        # Debug Mode
        debug_frame = ttk.LabelFrame(main_frame, text="🐛 Debug Mode", padding="10")
        debug_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.debug_var = tk.BooleanVar(value=self.config_manager.is_debug_mode())
        debug_check = ttk.Checkbutton(debug_frame, text="Enable debug output", variable=self.debug_var)
        debug_check.grid(row=0, column=0, sticky=tk.W)
        
        # Buttons - Make sure they're visible and properly styled
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Save button - Make it more prominent and ensure it's visible
        save_btn = tk.Button(button_frame, text="💾 Save Settings", command=lambda: self.save_settings(settings_window), 
                           bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), 
                           relief=tk.RAISED, bd=3, padx=20, pady=10)
        save_btn.grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", command=settings_window.destroy,
                             bg="#f44336", fg="white", font=("Arial", 12, "bold"),
                             relief=tk.RAISED, bd=3, padx=20, pady=10)
        cancel_btn.grid(row=0, column=1, sticky=tk.E)
        
        # Configure button frame columns to expand properly
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Force the buttons to be visible by updating the window
        settings_window.update()
        
        # Configure grid weights
        settings_window.columnconfigure(0, weight=1)
        settings_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(0, weight=1)
        
        # Apply dark mode styling to specific widgets after creation
        self.apply_dark_mode_to_settings_widgets(settings_window)
        
        # Force update to ensure buttons are visible
        settings_window.update_idletasks()
    
    def browse_eve_logs_path(self):
        """Browse for EVE logs directory"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Select EVE Chat Logs Folder")
        if directory:
            self.path_var.set(directory)
    
    def save_settings(self, settings_window):
        """Save settings to config.txt file"""
        try:
            # Validate inputs
            timer_value = self.timer_var.get().strip()
            if not timer_value.isdigit() or int(timer_value) < 1:
                from tkinter import messagebox
                messagebox.showerror("Invalid Input", "Game timer must be a positive number!")
                return
            
            # Validate EVE logs path if provided
            new_path = self.path_var.get().strip()
            if new_path and not os.path.exists(new_path):
                from tkinter import messagebox
                messagebox.showerror("Invalid Path", f"The path '{new_path}' does not exist!")
                return
            
            if new_path and not os.path.isdir(new_path):
                from tkinter import messagebox
                messagebox.showerror("Invalid Path", f"The path '{new_path}' is not a directory!")
                return
            
            # Check if path contains any .txt files
            if new_path:
                txt_files = [f for f in os.listdir(new_path) if f.endswith('.txt')]
                if not txt_files:
                    from tkinter import messagebox
                    result = messagebox.askyesno("No Chat Logs", 
                        f"The directory '{new_path}' contains no .txt files.\n\n"
                        "This might not be an EVE chat logs directory.\n\n"
                        "Do you want to continue anyway?")
                    if not result:
                        return
            
            # Read existing config or create new
            config_lines = []
            if os.path.exists('config.txt'):
                with open('config.txt', 'r', encoding='utf-8') as f:
                    config_lines = f.readlines()
            
            # Update or add settings
            new_lines = []
            settings_updated = {'EVE_LOGS_PATH': False, 'GAME_TIMER_MINUTES': False, 'DEBUG_MODE': False}
            
            for line in config_lines:
                if line.startswith('EVE_LOGS_PATH='):
                    new_lines.append(f"EVE_LOGS_PATH={self.path_var.get()}\n")
                    settings_updated['EVE_LOGS_PATH'] = True
                elif line.startswith('GAME_TIMER_MINUTES='):
                    new_lines.append(f"GAME_TIMER_MINUTES={timer_value}\n")
                    settings_updated['GAME_TIMER_MINUTES'] = True
                elif line.startswith('DEBUG_MODE='):
                    new_lines.append(f"DEBUG_MODE={str(self.debug_var.get()).lower()}\n")
                    settings_updated['DEBUG_MODE'] = True
                else:
                    new_lines.append(line)
            
            # Add new settings if they didn't exist
            if not settings_updated['EVE_LOGS_PATH']:
                new_lines.append(f"EVE_LOGS_PATH={self.path_var.get()}\n")
            if not settings_updated['GAME_TIMER_MINUTES']:
                new_lines.append(f"GAME_TIMER_MINUTES={timer_value}\n")
            if not settings_updated['DEBUG_MODE']:
                new_lines.append(f"DEBUG_MODE={str(self.debug_var.get()).lower()}\n")
            
            # Write updated config
            with open('config.txt', 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Reload config
            self.config_manager.load_config()
            
            # Restart monitoring with new path if it changed
            old_path = self.config_manager.get_eve_logs_path()
            if new_path != old_path:
                self.restart_monitoring(new_path)
            
            # Show success message
            from tkinter import messagebox
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!\n\nMonitoring has been updated to use the new path.")
            
            # Close the settings window
            settings_window.destroy()
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            print(f"Error saving settings: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_section(self, section):
        """Toggle the visibility of a section (collapse/expand)"""
        if section == "instructions":
            if self.instructions_collapsed:
                # Expand
                self.instructions_content_frame.grid()
                self.instructions_collapsed = False
                # Update button text
                for child in self.instructions_content_frame.master.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(text="🔽 Hide")
            else:
                # Collapse
                self.instructions_content_frame.grid_remove()
                self.instructions_collapsed = True
                # Update button text
                for child in self.instructions_content_frame.master.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(text="▶️ Show")
    
    def apply_dark_mode(self):
        """Apply dark mode styling to the application"""
        try:
            # Configure ttk styles for dark mode
            style = ttk.Style()
            
            # Try to use clam theme, fallback to default if not available
            try:
                style.theme_use('clam')  # Use clam theme as base
            except Exception as e:
                print(f"Warning: 'clam' theme not available: {e}")
            
            # Configure the root window
            try:
                self.root.configure(bg="#1e1e1e")
            except Exception as e:
                print(f"Warning: Could not set root background: {e}")
            
            # Configure frame styles with error handling
            try:
                style.configure('TFrame', background='#1e1e1e')
                style.configure('TLabelframe', background='#1e1e1e', foreground='white')
                style.configure('TLabelframe.Label', background='#1e1e1e', foreground='white')
                style.configure('TLabel', background='#1e1e1e', foreground='white')
            except Exception as e:
                print(f"Warning: Could not configure frame/label styles: {e}")
            
            # Configure button styles with error handling
            try:
                style.configure('TButton', background='#404040', foreground='white')
                style.map('TButton', 
                         background=[('active', '#505050'), ('pressed', '#303030')],
                         foreground=[('active', 'white'), ('pressed', 'white')])
            except Exception as e:
                print(f"Warning: Could not configure button styles: {e}")
            
            # Configure treeview styles with error handling
            try:
                style.configure('Treeview', background='#2b2b2b', foreground='white', fieldbackground='#2b2b2b')
                style.configure('Treeview.Heading', background='#404040', foreground='white')
                style.map('Treeview', 
                         background=[('selected', '#505050')],
                         foreground=[('selected', 'white')])
            except Exception as e:
                print(f"Warning: Could not configure treeview styles: {e}")
            
            # Configure scrollbar styles with error handling
            try:
                style.configure('Vertical.TScrollbar', background='#404040', troughcolor='#2b2b2b')
                style.map('Vertical.TScrollbar', 
                         background=[('active', '#505050'), ('pressed', '#303030')])
            except Exception as e:
                print(f"Warning: Could not configure scrollbar styles: {e}")
            
            # Configure additional dark mode styles for settings window
            try:
                style.configure('Dark.TLabelframe', background='#1e1e1e', foreground='white')
                style.configure('Dark.TLabelframe.Label', background='#1e1e1e', foreground='white')
                style.configure('Dark.TLabel', background='#1e1e1e', foreground='white')
                style.configure('Dark.TButton', background='#404040', foreground='white')
                style.configure('Dark.TEntry', fieldbackground='#2b2b2b', foreground='white', insertbackground='white')
                style.configure('Dark.TCheckbutton', background='#1e1e1e', foreground='white')
                
                # Force Entry widget styling
                style.map('Dark.TEntry',
                         fieldbackground=[('readonly', '#2b2b2b'), ('focus', '#2b2b2b')],
                         foreground=[('readonly', 'white'), ('focus', 'white')])
                
                # Force Button widget styling
                style.map('Dark.TButton',
                         background=[('active', '#505050'), ('pressed', '#303030')],
                         foreground=[('active', 'white'), ('pressed', 'white')])
                
            except Exception as e:
                print(f"Warning: Could not configure dark mode styles: {e}")
                
        except Exception as e:
            print(f"Warning: Could not apply dark mode styling: {e}")
            print("Using default system styling instead.")
    
    def apply_dark_mode_to_window(self, window):
        """Apply dark mode styling to a specific window (like settings)"""
        try:
            # Configure the window background
            try:
                window.configure(bg="#1e1e1e")
            except Exception as e:
                print(f"Warning: Could not set window background: {e}")
            
            # Apply dark mode to all child widgets recursively
            self.apply_dark_mode_to_widgets(window)
            
        except Exception as e:
            print(f"Warning: Could not apply dark mode to window: {e}")
    
    def apply_dark_mode_to_widgets(self, parent):
        """Recursively apply dark mode to all child widgets"""
        try:
            for child in parent.winfo_children():
                try:
                    # Apply dark mode based on widget type
                    if isinstance(child, tk.Label):
                        child.configure(bg="#1e1e1e", fg="white")
                    elif isinstance(child, tk.Entry):
                        child.configure(bg="#2b2b2b", fg="white", insertbackground="white")
                    elif isinstance(child, tk.Checkbutton):
                        child.configure(bg="#1e1e1e", fg="white", selectcolor="#404040")
                    elif isinstance(child, tk.Button):
                        child.configure(bg="#404040", fg="white", activebackground="#505050", activeforeground="white")
                    elif isinstance(child, tk.Frame) or isinstance(child, ttk.Frame):
                        child.configure(bg="#1e1e1e")
                    elif isinstance(child, ttk.LabelFrame):
                        child.configure(style='Dark.TLabelframe')
                    elif isinstance(child, ttk.Label):
                        child.configure(style='Dark.TLabel')
                    elif isinstance(child, ttk.Button):
                        child.configure(style='Dark.TButton')
                    elif isinstance(child, ttk.Entry):
                        child.configure(style='Dark.TCheckbutton')
                except Exception as e:
                    # Continue with other widgets if one fails
                    pass
                
                # Recursively apply to children
                self.apply_dark_mode_to_widgets(child)
                
        except Exception as e:
            print(f"Warning: Could not apply dark mode to widgets: {e}")
    
    def apply_dark_mode_to_settings_widgets(self, settings_window):
        """Apply dark mode specifically to settings window widgets"""
        try:
            # Find and style the Entry widgets specifically
            for widget in settings_window.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.LabelFrame):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Entry):
                                    # Force dark styling for Entry widgets
                                    grandchild.configure(style='Dark.TEntry')
                                    # Also try direct configuration as fallback
                                    try:
                                        grandchild.configure(background="#2b2b2b", foreground="white", insertbackground="white")
                                    except:
                                        pass
                                elif isinstance(grandchild, ttk.Button):
                                    grandchild.configure(style='Dark.TButton')
                                elif isinstance(grandchild, ttk.Label):
                                    grandchild.configure(style='Dark.TLabel')
                                elif isinstance(grandchild, ttk.Checkbutton):
                                    grandchild.configure(style='Dark.TCheckbutton')
                        elif isinstance(child, ttk.Button):
                            child.configure(style='Dark.TButton')
                        elif isinstance(child, ttk.Label):
                            child.configure(style='Dark.TLabel')
            
            # Ensure the button frame is visible
            button_frame = None
            for widget in settings_window.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame) and len(child.winfo_children()) > 0:
                            # Check if this is the button frame (has buttons)
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Button) and "Save" in grandchild.cget("text"):
                                    button_frame = child
                                    break
                            if button_frame:
                                break
                    if button_frame:
                        break
            
            if button_frame:
                # Make sure button frame is visible and properly styled
                button_frame.configure(style='Dark.TFrame')
                print("DEBUG: Button frame found and styled")
            else:
                print("DEBUG: Button frame not found")
                
        except Exception as e:
            print(f"Warning: Could not apply dark mode to settings widgets: {e}")
            import traceback
            traceback.print_exc()
    
    def sort_column(self, column):
        """Sort the participants tree by the specified column"""
        # Get all items from the tree
        items = [(self.participants_tree.set(item, column), item) for item in self.participants_tree.get_children('')]
        
        # Sort items based on column type
        if column == 'Username':
            # Sort alphabetically
            items.sort(key=lambda x: x[0].lower())
        elif column == 'Guess':
            # Sort numerically
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        elif column == 'Time':
            # Sort by time (HH:MM:SS format)
            items.sort(key=lambda x: x[0])
        
        # Reverse if already sorted in this direction
        if self.sort_directions[column]:
            items.reverse()
            self.sort_directions[column] = False
        else:
            self.sort_directions[column] = True
        
        # Rearrange items in the tree
        for index, (val, item) in enumerate(items):
            self.participants_tree.move(item, '', index)
        
        # Update column header to show sort direction
        current_text = self.participants_tree.heading(column)['text']
        if self.sort_directions[column]:
            self.participants_tree.heading(column, text=f"{current_text} ↓")
        else:
            self.participants_tree.heading(column, text=f"{current_text} ↑")
    
    def update_game_status(self, message):
        """Thread-safe game status update"""
        if hasattr(self, 'root') and self.root:
            self.root.after(0, self._update_game_status_safe, message)
    
    def _update_game_status_safe(self, message):
        """Internal method to update game status (called from main thread)"""
        try:
            self.status_text.delete(1.0, tk.END)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.status_text.insert(tk.END, f"[{timestamp}] {message}")
            self.status_text.see(tk.END)
        except Exception as e:
            print(f"Error updating game status: {e}")
    
    def add_participant(self, username, guess):
        """Thread-safe participant addition"""
        if hasattr(self, 'root') and self.root:
            self.root.after(0, self._add_participant_safe, username, guess)
    
    def _add_participant_safe(self, username, guess):
        """Internal method to add participant (called from main thread)"""
        try:
            time_str = datetime.now().strftime('%H:%M:%S')
            print(f"DEBUG: GUI adding participant {username} with guess {guess} at {time_str}")
            self.participants_tree.insert('', 'end', values=(username, guess, time_str))
            print(f"DEBUG: Participant tree now has {len(self.participants_tree.get_children())} entries")
        except Exception as e:
            print(f"Error adding participant: {e}")
    
    def clear_participants(self):
        """Thread-safe participant clearing"""
        if hasattr(self, 'root') and self.root:
            self.root.after(0, self._clear_participants_safe)
    
    def _clear_participants_safe(self):
        """Internal method to clear participants (called from main thread)"""
        try:
            for item in self.participants_tree.get_children():
                self.participants_tree.delete(item)
        except Exception as e:
            print(f"Error clearing participants: {e}")
    
    def load_window_settings(self):
        """Load saved window size and position from settings file"""
        try:
            if os.path.exists('window_settings.json'):
                with open('window_settings.json', 'r') as f:
                    settings = json.load(f)
                    geometry = settings.get('geometry', '1200x800')
                    x = settings.get('x', 100)
                    y = settings.get('y', 100)
                    self.root.geometry(geometry)
                    self.root.geometry(f"+{x}+{y}")
            else:
                # Default size if no settings file
                self.root.geometry("1200x800+100+100")
        except Exception as e:
            print(f"Error loading window settings: {e}")
            # Fallback to default size
            self.root.geometry("1200x800+100+100")
    
    def save_window_settings(self):
        """Save current window size and position to settings file"""
        try:
            geometry = self.root.geometry()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            
            settings = {
                'geometry': geometry,
                'x': x,
                'y': y
            }
            
            with open('window_settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving window settings: {e}")
    
    def on_closing(self):
        """Handle window closing - save settings and cleanup"""
        self.save_window_settings()
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EVEGiveawayGUI()
    app.run()