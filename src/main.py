import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
import random
import time
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import json

class EVEChatMonitor(FileSystemEventHandler):
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.eve_logs_path = os.path.expanduser("~/Documents/EVE/logs/Chatlogs")
        self.current_files = {}
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            self.process_chat_log(event.src_path)
    
    def process_chat_log(self, file_path):
        try:
            # EVE Online uses UTF-16 encoding - try this first
            encodings = ['utf-16', 'utf-8', 'cp1252', 'iso-8859-1']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        lines = f.readlines()
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
                        print(f"DEBUG: Original line: '{last_line[:100]}...'")
                        print(f"DEBUG: Cleaned line: '{cleaned_line}'")
                        self.parse_message(cleaned_line)
        except Exception as e:
            print(f"Error reading chat log: {e}")
    
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
        # Parse EVE chat format: [ timestamp ] CharacterName > message
        pattern = r'\[ ([\d\.]+ [\d:]+) \] ([^>]+) > (.+)'
        match = re.match(pattern, message)
        
        if match:
            timestamp, character_name, content = match.groups()
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
            print(f"DEBUG: Message did not match pattern: '{message}'")

class GameManager:
    def __init__(self, gui):
        self.gui = gui
        self.current_game = None
        self.participants = {}
        self.admin_users = set()  # Add admin usernames here
        
    def start_pir_game(self, admin_name, command):
        if not self.is_admin(admin_name):
            return
            
        try:
            # Handle case-insensitive command parsing using regex
            import re
            range_match = re.search(r'!pir\s+(\d+-\d+)', command, re.IGNORECASE)
            if range_match:
                range_str = range_match.group(1)
                min_val, max_val = map(int, range_str.split('-'))
                target = random.randint(min_val, max_val)
                
                self.current_game = {
                    'type': 'PIR',
                    'admin': admin_name,
                    'range': f"{min_val}-{max_val}",
                    'target': target,
                    'start_time': datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=2),
                    'participants': {},
                    'active': True
                }
                
                self.gui.update_game_status(f"🎯 Price is Right game started by {admin_name}!\nRange: {min_val}-{max_val}\n⏰ Game ends in 5 minutes!\nPlayers use ?number to enter!")
                self.gui.clear_participants()
                
                # Start the game timer
                self.start_game_timer()
                
        except Exception as e:
            print(f"Error starting PIR game: {e}")
    
    def start_gtn_game(self, admin_name, command):
        if not self.is_admin(admin_name):
            return
            
        try:
            # Handle case-insensitive command parsing using regex
            import re
            range_match = re.search(r'!gtn\s+(\d+-\d+)', command, re.IGNORECASE)
            if range_match:
                range_str = range_match.group(1)
                min_val, max_val = map(int, range_str.split('-'))
                target = random.randint(min_val, max_val)
                
                self.current_game = {
                    'type': 'GTN',
                    'admin': admin_name,
                    'range': f"{min_val}-{max_val}",
                    'target': target,
                    'start_time': datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=2),
                    'participants': {},
                    'active': True
                }
                
                self.gui.update_game_status(f"🎲 Guess the Number game started by {admin_name}!\nRange: {min_val}-{max_val}\n⏰ Game ends in 5 minutes!\nPlayers use ?number to enter!")
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
        if not self.is_admin(admin_name) or not self.current_game:
            return
            
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
        
        self.current_game['active'] = False
    
    def clear_game(self, admin_name):
        if not self.is_admin(admin_name):
            return
            
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
        if not self.is_admin(admin_name):
            return
            
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
            # Read admin list from external file
            if os.path.exists('admins.txt'):
                with open('admins.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            admin_list.add(line)
            else:
                # Fallback to default admin if file doesn't exist
                print("Warning: admins.txt not found, using default admin list")
                admin_list = {'Hamilton Norris'}
            
            return username in admin_list
        except Exception as e:
            print(f"Error reading admin list: {e}")
            # Fallback to default admin if there's an error
            return username == 'Hamilton Norris'
    
    def start_game_timer(self):
        """Start a timer that will automatically end the game after 5 minutes"""
        def timer_thread():
            while self.current_game and self.current_game['active']:
                time.sleep(1)  # Check every second
                if datetime.now() >= self.current_game['end_time']:
                    # Game time is up!
                    if self.current_game['active']:
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
        
        # Start timer in a separate thread
        timer_thread = threading.Thread(target=timer_thread, daemon=True)
        timer_thread.start()

class EVEGiveawayGUI:
    def __init__(self):
        try:
            self.root = tk.Tk()
            self.root.title("EVE Online Giveaway Tool")
            
            # Set a minimum window size to prevent layout issues
            self.root.minsize(800, 600)
            
            # Load saved window size and position
            self.load_window_settings()
            
            # Game manager
            self.game_manager = GameManager(self)
            
            # Chat monitor
            self.chat_monitor = EVEChatMonitor(self.game_manager)
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
        
        self.status_text = tk.Text(status_frame, height=6, width=90, font=("Consolas", 10), 
                                  bg="#2b2b2b", fg="white", insertbackground="white")
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Countdown timer display
        self.countdown_label = ttk.Label(status_frame, text="⏰ No active game", font=("Arial", 12, "bold"), foreground="white")
        self.countdown_label.grid(row=1, column=0, pady=(5, 0))
        
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
        
        self.status_text = tk.Text(status_frame, height=6, width=90, font=("Consolas", 10), 
                                  bg="#2b2b2b", fg="white", insertbackground="white")
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Countdown timer display
        self.countdown_label = ttk.Label(status_frame, text="⏰ No active game", font=("Arial", 12, "bold"), foreground="white")
        self.countdown_label.grid(row=1, column=0, pady=(5, 0))
        
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
        eve_logs_path = os.path.expanduser("~/Documents/EVE/logs/Chatlogs")
        
        if os.path.exists(eve_logs_path):
            self.observer = Observer()
            self.observer.schedule(self.chat_monitor, eve_logs_path, recursive=False)
            self.observer.start()
            self.update_game_status("🔍 Monitoring EVE chat logs...\n✅ Ready for games!\n\nUse !PIR or !GTN to start a game!")
            
            # Start countdown timer update
            self.start_countdown_timer()
        else:
            self.update_game_status(f"❌ EVE logs directory not found: {eve_logs_path}\nPlease make sure EVE Online is installed.")
    
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
                
        except Exception as e:
            print(f"Warning: Could not apply dark mode styling: {e}")
            print("Using default system styling instead.")
    
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
        self.status_text.delete(1.0, tk.END)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_text.insert(tk.END, f"[{timestamp}] {message}")
        self.status_text.see(tk.END)
    
    def add_participant(self, username, guess):
        time_str = datetime.now().strftime('%H:%M:%S')
        print(f"DEBUG: GUI adding participant {username} with guess {guess} at {time_str}")
        self.participants_tree.insert('', 'end', values=(username, guess, time_str))
        print(f"DEBUG: Participant tree now has {len(self.participants_tree.get_children())} entries")
    
    def clear_participants(self):
        for item in self.participants_tree.get_children():
            self.participants_tree.delete(item)
    
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