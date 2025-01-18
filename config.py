# config.py
import os
import json
from datetime import datetime 

DEFAULT_CONFIG = {
    'selected_calendar': None,
    'working_hours': {
        'start': '11:00',
        'end': '19:00'
    },
    'last_location': ''
}

CONFIG_FILE = os.path.expanduser('~/.meeting_coordinator_config.json')

def load_config():
    """Load configuration from file or create default if it doesn't exist"""
    try:
        # Force clear any OS file caching
        if os.path.exists(CONFIG_FILE):
            os.fsync(os.open(CONFIG_FILE, os.O_RDONLY))
            
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # print(f"Loaded config from file: {config}")
            return config
    except FileNotFoundError:
        print("Config file not found, using default")
        print(f"Debug - Trying to load from: {os.path.abspath(CONFIG_FILE)}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def setup_initial_config(calendars):
    """Interactive configuration setup"""
    config = load_config()
    
    print("\nAvailable calendars:")
    for i, calendar in enumerate(calendars, 1):
        print(f"{i}. {calendar}")
    
    while True:
        try:
            choice = input("\nSelect your primary calendar (enter the number): ")
            index = int(choice) - 1
            if 0 <= index < len(calendars):
                config['selected_calendar'] = calendars[index]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Working hours setup
    print("\nCurrent working hours:", config['working_hours'])
    change = input("Would you like to change working hours? (y/n): ").lower()
    if change == 'y':
        while True:
            start = input("Enter start time (HH:MM, 24h format): ")
            end = input("Enter end time (HH:MM, 24h format): ")
            try:
                # Basic validation of time format
                datetime.strptime(start, '%H:%M')
                datetime.strptime(end, '%H:%M')
                config['working_hours'] = {'start': start, 'end': end}
                break
            except ValueError:
                print("Invalid time format. Please use HH:MM (e.g., 09:00)")
    
    save_config(config)
    return config