from setuptools import setup

APP = ['gui.py']
DATA_FILES = [
    ('resources', ['resources/icon_64x64.png', 'resources/icon_128x128.png', 
                  'resources/calendar-search.png', 'resources/settings.png', 
                  'resources/log-out.png'])
]
OPTIONS = {
    'argv_emulation': True,
    'argv_emulation': True,
    'packages': ['PyQt5', 'pytz', 'geopy', 'timezonefinder'],
    'includes': ['Foundation', 'EventKit'],
    'excludes': ['pkg_resources', 'setuptools'], 
    'iconfile': 'resources/icon.icns',
    'plist': {
        'CFBundleName': 'Meeting Coordinator',
        'CFBundleDisplayName': 'Meeting Coordinator',
        'CFBundleIdentifier': 'com.yourcompany.meetingcoordinator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.13',
        'NSCalendarsUsageDescription': 'Access calendar to check availability',
        'LSUIElement': True
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)