#!/usr/bin/env python3
"""
Simple test GUI for EVE Giveaway Tool
Use this to test if basic GUI functionality works on the user's system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys

def create_test_gui():
    """Create a minimal test GUI"""
    try:
        # Create root window
        root = tk.Tk()
        root.title("EVE Giveaway Tool - Test GUI")
        root.geometry("800x600")
        root.minsize(600, 400)
        
        # Try to set a dark background (with fallback)
        try:
            root.configure(bg='#2b2b2b')
        except:
            root.configure(bg='gray')
        
        # Main frame
        main_frame = tk.Frame(root, bg=root.cget('bg'))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🎮 EVE Giveaway Tool - Test Mode", 
                              font=("Arial", 18, "bold"), 
                              bg=root.cget('bg'), fg='white')
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = tk.LabelFrame(main_frame, text="🎯 Game Status", 
                                   bg=root.cget('bg'), fg='white')
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Status text
        status_text = tk.Text(status_frame, height=8, width=70, 
                             font=("Consolas", 10),
                             bg='#2b2b2b', fg='white', insertbackground='white')
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some test content
        status_text.insert(tk.END, "✅ GUI Test Successful!\n\n")
        status_text.insert(tk.END, "This is a test window to verify basic GUI functionality.\n")
        status_text.insert(tk.END, "If you can see this text, the GUI is working.\n\n")
        status_text.insert(tk.END, "Common issues that cause white screens:\n")
        status_text.insert(tk.END, "• Missing tkinter installation\n")
        status_text.insert(tk.END, "• Display driver issues\n")
        status_text.insert(tk.END, "• Windows theme conflicts\n")
        status_text.insert(tk.END, "• Python installation problems\n\n")
        status_text.insert(tk.END, "Try running the main application now.\n")
        
        # Test button
        test_button = tk.Button(main_frame, text="🧪 Test Button", 
                               command=lambda: messagebox.showinfo("Test", "Button click works!"),
                               bg='#404040', fg='white', font=("Arial", 12))
        test_button.pack(pady=10)
        
        # Close button
        close_button = tk.Button(main_frame, text="❌ Close Test", 
                                command=root.destroy,
                                bg='#800000', fg='white', font=("Arial", 12))
        close_button.pack(pady=5)
        
        # Info label
        info_label = tk.Label(main_frame, text="If this window displays correctly, the main app should work too.",
                             bg=root.cget('bg'), fg='white', font=("Arial", 10))
        info_label.pack(pady=10)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error creating test GUI: {e}")
        messagebox.showerror("Error", f"Failed to create test GUI: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting GUI test...")
    print("If you see a white screen, there's a system-level issue.")
    print("If you see a normal window, the main app should work.")
    
    try:
        success = create_test_gui()
        if success:
            print("Test GUI completed successfully.")
        else:
            print("Test GUI failed.")
    except Exception as e:
        print(f"Critical error: {e}")
        input("Press Enter to exit...")
