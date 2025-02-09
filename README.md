# Meeting Coordinator

A macOS menu bar application for finding and communicating meeting availability across time zones.

## Features
- macOS Calendar integration 
- Multiple date selection
- Automatic timezone detection
- Configurable working hours
- Email-friendly output

## Installation
1. Download latest [release](https://github.com/Amir5f/meeting-coordinator/releases)
2. Move to Applications
3. Right-click > Open (first time)
4. Grant calendar access when prompted

## Requirements
- macOS 10.13+
- Configured Calendar app

## Usage
1. Click menu bar icon
2. Select calendar and dates
3. Set meeting duration
4. Enter location for timezone
5. Click "Check Availability"
6. Copy generated text

## Build from Source
```bash
# Clone
git clone https://github.com/Amir5f/meeting-coordinator.git

# Setup venv
python3 -m venv venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Build
python3 setup.py py2app
