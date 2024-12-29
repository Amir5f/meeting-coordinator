import sys
import os
import json
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSystemTrayIcon, 
    QMenu, QAction, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QSpinBox, QDateEdit, 
    QComboBox, QMessageBox, QGroupBox, QGridLayout, QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from datetime import datetime, timedelta
from config import load_config, setup_initial_config
import pytz
from main import (list_calendars, get_events_for_date, parse_calendar_events,
                 get_available_slots, format_multiple_days_email, get_location_timezone)


class SettingsWindow(QWidget):
    def __init__(self, current_config, menu_instance):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setStyleSheet(STYLESHEET)
        self.current_config = current_config
        self.menu_instance = menu_instance  # Changed name to be more explicit
        self.current_start_time = current_config['working_hours']['start']
        self.current_end_time = current_config['working_hours']['end']
        
        self.setup_ui()
    
    def on_start_time_changed(self, text):
        print(f"Start time changed to: {text}")
        self.current_start_time = text  # Store the new value
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Calendar Selection
        calendar_group = QGroupBox("Default Calendar")
        calendar_layout = QVBoxLayout()
        self.calendar_combo = QComboBox()
        available_calendars = list_calendars()
        self.calendar_combo.addItems(available_calendars)
        if self.current_config['selected_calendar'] in available_calendars:
            current_index = available_calendars.index(self.current_config['selected_calendar'])
            self.calendar_combo.setCurrentIndex(current_index)
        calendar_layout.addWidget(self.calendar_combo)
        calendar_group.setLayout(calendar_layout)
        layout.addWidget(calendar_group)
        
        # Working Hours
        hours_group = QGroupBox("Working Hours")
        hours_layout = QGridLayout()
        hours_layout.setContentsMargins(10, 10, 10, 10)  # Add margins
        hours_layout.setVerticalSpacing(10)  # Add spacing between rows
        
        # Start time
        hours_layout.addWidget(QLabel("Start:"), 0, 0)
        self.start_time = QLineEdit()
        self.start_time.setMinimumHeight(32)
        self.start_time.setText(self.current_config['working_hours']['start'])
        self.start_time.textChanged.connect(self.on_start_time_changed)  # Connect to our tracking method
        hours_layout.addWidget(self.start_time, 0, 1)


        # End time
        hours_layout.addWidget(QLabel("End:"), 1, 0)
        self.end_time = QLineEdit()  # Create empty first
        self.end_time.setMinimumHeight(32)
        self.end_time.setText(self.current_config['working_hours']['end'])  # Set text after
        self.end_time.textChanged.connect(lambda text: print(f"End time changed to: {text}"))
        hours_layout.addWidget(self.end_time, 1, 1)
        
        hours_group.setLayout(hours_layout)  # Add this line!
        layout.addWidget(hours_group)  # And add the group to the main layout
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        self.setFixedSize(300, 250)

        
    def save_settings(self):
        # Get current values
        start_time = self.start_time.text().strip()
        end_time = self.end_time.text().strip()
        selected_calendar = self.calendar_combo.currentText()
        
        print(f"About to save - Start: {start_time}, End: {end_time}")  # Debug

        new_config = {
            'selected_calendar': selected_calendar,
            'working_hours': {
                'start': start_time,
                'end': end_time
            }
        }
        
        # Validate working hours format (HH:MM)
        time_format = "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not (re.match(time_format, new_config['working_hours']['start']) and 
                re.match(time_format, new_config['working_hours']['end'])):
            QMessageBox.warning(self, "Invalid Time Format", 
                            "Please enter times in HH:MM format (e.g., 09:00)")
            return
                
        try:
            # Save to file
            # Import the CONFIG_FILE path
            from config import CONFIG_FILE, save_config
            
            # Use the save_config function from config.py
            save_config(new_config)
            print(f"Debug - Saved to: {CONFIG_FILE}")
            
            # Update configs everywhere
            self.menu_instance.refresh_config()
            
            # Show success message
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.close()
        except Exception as e:
            print(f"Debug - Save error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
        
# Set QT_MAC_WANTS_LAYER for macOS
if sys.platform == 'darwin':
    os.environ['QT_MAC_WANTS_LAYER'] = '1'

STYLESHEET = """
QComboBox {
    padding: 6px;
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    background-color: #2D2D2D;
    color: #D4D4D4;
}
QGroupBox {
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
}
QGroupBox::title {
    color: #D4D4D4;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}

QWidget {
    background-color: #1E1E1E;  /* VSCode dark background */
    color: #D4D4D4;  /* VSCode default text color */
}
QPushButton {
    background-color: #0078D4;  /* Microsoft blue */
    color: white;
    border: none;
    padding: 8px;
    border-radius: 4px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #106EBE;
}
QLineEdit, QSpinBox, QDateEdit {
    padding: 6px;
    border: 1px solid #3C3C3C;  /* VSCode border color */
    border-radius: 4px;
    background-color: #2D2D2D;  /* VSCode input background */
    color: #D4D4D4;  /* VSCode text color */
}
QTextEdit {
    background-color: #2D2D2D;  /* VSCode input background */
    color: #D4D4D4;  /* VSCode text color */
    border: 1px solid #3C3C3C;
    border-radius: 4px;
    padding: 4px;
}
QLabel {
    color: #D4D4D4;  /* VSCode text color */
}
QMenu {
    background-color: #1E1E1E;  /* VSCode dark background */
    color: #D4D4D4;  /* VSCode text color */
    border: 1px solid #3C3C3C;
}
QMenu::item:selected {
    background-color: #2D2D2D;  /* VSCode selection color */
}
"""

class MeetingCoordinatorMenu(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        #print(f"Debug - MeetingCoordinatorMenu methods: {dir(self)}")

        # Load configuration
        self.config = load_config()
        if self.config is None:
            self.config = setup_initial_config(list_calendars())
        
        
        # Create a simple icon programmatically
        from PyQt5.QtGui import QPixmap, QPainter, QColor
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.transparent)
        painter = QPainter(icon_pixmap)
        painter.setBrush(QColor('#0078D4'))  # Blue color
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(8, 8, 48, 48)  # Draw a circle
        painter.end()
        self.setIcon(QIcon(icon_pixmap))
        
        # Create the tray menu
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        
        # Add actions to menu
        self.setup_menu()
        
        # Create the main window (hidden by default)
        self.window = CheckAvailabilityWindow()
        
        self.show()

    def refresh_config(self):
        self.config = load_config()
        print(f"Menu refreshed with config: {self.config}")
        if hasattr(self, 'window'):
            self.window.refresh_config()

    def setup_menu(self):
        # Apply dark theme to menu
        self.menu.setStyleSheet(STYLESHEET)
        
        # Add menu items
        check_action = QAction("Check Availability", self)
        check_action.triggered.connect(self.show_window)
        self.menu.addAction(check_action)
        
        self.menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        self.menu.addAction(settings_action)
        
        self.menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(app.quit)
        self.menu.addAction(quit_action)
        
    def show_settings(self):
        self.config = load_config()  # Ensure we have latest config
        print(f"Opening settings with config: {self.config}")  # Debug
        self.settings_window = SettingsWindow(self.config, self)  # Pass self (the menu instance)
        self.settings_window.show()

    def show_window(self):
        # Get the geometry of the menu bar icon
        geometry = self.geometry()
        
        # Position the window just below the menu bar
        window_x = geometry.x() - (self.window.width() // 2)  # Center horizontally with the icon
        window_y = 25  # Fixed distance from top of screen for macOS menu bar
            
        # Ensure the window stays within screen bounds
        screen = QApplication.primaryScreen().geometry()
        if window_x + self.window.width() > screen.width():
            window_x = screen.width() - self.window.width()
        if window_x < 0:
            window_x = 0
                
        self.window.move(window_x, window_y)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

class CheckAvailabilityWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Check Availability")
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Initialize configuration
        self.config = load_config()
        self.available_calendars = list_calendars()
        self.date_widgets = []

        # Working hours state
        self.temp_working_hours = None  # Will store temporary override
        
        # Setup UI
        self.setup_ui()
        
    def refresh_config(self):
        self.config = load_config()
        self.available_calendars = list_calendars()
        current_cal_index = self.available_calendars.index(self.config['selected_calendar'])
        self.calendar_combo.setCurrentIndex(current_cal_index)

    def show_settings(self):
        self.config = load_config()  # Ensure we have latest config
        print(f"Opening settings with config: {self.config}")  # Debug
        print(f"Debug - self in show_settings: {self}")  # Add this line
        self.settings_window = SettingsWindow(self.config, self)
        self.settings_window.show()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Calendar selection
        calendar_layout = QHBoxLayout()
        calendar_label = QLabel("Calendar:")
        self.calendar_combo = QComboBox()
        self.calendar_combo.addItems(self.available_calendars)
        current_cal_index = self.available_calendars.index(self.config['selected_calendar'])
        self.calendar_combo.setCurrentIndex(current_cal_index)
        calendar_layout.addWidget(calendar_label)
        calendar_layout.addWidget(self.calendar_combo)
        layout.addLayout(calendar_layout)

        # Working Hours Override Group
        hours_group = QGroupBox("Working Hours")
        hours_layout = QGridLayout()
        hours_layout.setContentsMargins(10, 10, 10, 10)  
        hours_layout.setVerticalSpacing(10)
        
        # Override checkbox
        self.override_checkbox = QCheckBox("Override default working hours")
        self.override_checkbox.stateChanged.connect(self.toggle_working_hours_override)
        hours_layout.addWidget(self.override_checkbox)
        
        # NEW: Override checkbox
        self.override_checkbox = QCheckBox("Use temporary hours")
        self.override_checkbox.stateChanged.connect(self.toggle_working_hours_override)
        hours_layout.addWidget(self.override_checkbox, 0, 0, 1, 2)
        
        # NEW: Time inputs
        hours_layout.addWidget(QLabel("Start:"), 1, 0)
        self.temp_start_time = QLineEdit()
        self.temp_start_time = QLineEdit(self.config['working_hours']['start'])
        self.temp_start_time.setMinimumWidth(100)
        self.temp_start_time.setMinimumHeight(32)
        self.temp_start_time.setEnabled(False)
        hours_layout.addWidget(self.temp_start_time, 1, 1)
        
        hours_layout.addWidget(QLabel("End:"), 2, 0)
        self.temp_end_time = QLineEdit()
        self.temp_end_time = QLineEdit(self.config['working_hours']['end'])
        self.temp_end_time.setMinimumWidth(100)
        self.temp_end_time.setMinimumHeight(32)
        self.temp_end_time.setEnabled(False)
        hours_layout.addWidget(self.temp_end_time, 2, 1)
        
        hours_group.setLayout(hours_layout)
        layout.addWidget(hours_group)

        # Date selection
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setMinimumDate(QDate.currentDate())
        date_edit.setMinimumHeight(32)
        self.date_widgets.append(date_edit)
        layout.addWidget(date_edit)
        
        # Duration input
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Duration (minutes):")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 480)
        self.duration_input.setValue(60)
        self.duration_input.setMinimumHeight(32)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_input)
        layout.addLayout(duration_layout)
        
        # Location input
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city or location (e.g., 'London, UK')")
        self.location_input.setMinimumHeight(32)
        layout.addWidget(self.location_input)
        
        # Check button
        check_button = QPushButton("Check Availability")
        check_button.setMinimumHeight(40)
        check_button.clicked.connect(self.check_availability)
        layout.addWidget(check_button)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Available time slots will appear here...")
        self.results_text.setMaximumHeight(80)
        layout.addWidget(self.results_text)
        
        # Copy button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_button)
        
        self.setFixedSize(300, 500)  # Increased height for calendar selection

    # NEW: Add these methods to CheckAvailabilityWindow
    def toggle_working_hours_override(self, state):
        """Enable/disable temporary working hours override"""
        enabled = bool(state)
        self.temp_start_time.setEnabled(enabled)
        self.temp_end_time.setEnabled(enabled)
        
        if enabled:
            self.temp_start_time.setText(self.config['working_hours']['start'])
            self.temp_end_time.setText(self.config['working_hours']['end'])
        else:
            self.temp_start_time.clear()
            self.temp_end_time.clear()

    def get_working_hours(self):
        """Get either temporary or default working hours"""
        if self.override_checkbox.isChecked():
            start = self.temp_start_time.text().strip()
            end = self.temp_end_time.text().strip()
            
            time_format = "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
            if not (re.match(time_format, start) and re.match(time_format, end)):
                QMessageBox.warning(self, "Invalid Time Format", 
                                "Please enter times in HH:MM format (e.g., 09:00)")
                return None
                
            return {'start': start, 'end': end}
        
        return self.config['working_hours']
    
    def check_availability(self):
        self.results_text.clear()
        
        # NEW: Get working hours (temporary or default)
        working_hours = self.get_working_hours()
        if working_hours is None:
            return

        try:
            # Get selected calendar
            selected_calendar = self.calendar_combo.currentText()
            
            # Get selected dates
            selected_dates = []
            for date_widget in self.date_widgets:
                qdate = date_widget.date()
                date = datetime(qdate.year(), qdate.month(), qdate.day())
                selected_dates.append(date)
            
            # Get duration
            duration = self.duration_input.value()
            
            # Get location and convert to timezone
            location = self.location_input.text()
            timezone_str = None
            if location:
                timezone_str = get_location_timezone(location)
                if not timezone_str:
                    self.results_text.setText("Could not determine timezone for the given location.")
                    return
                
            # Check availability for each date
            all_available_slots = {}
            for target_date in selected_dates:
                available_slots = get_available_slots(
                    selected_calendar,
                    target_date,
                    working_hours,
                    duration,
                    timezone_str
                )
                all_available_slots[target_date.date()] = available_slots
            
            # Format results
            results = format_multiple_days_email(all_available_slots, timezone_str)
            self.results_text.setText(results)
            
        except Exception as e:
            self.results_text.setText(f"An error occurred: {str(e)}")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.results_text.toPlainText())

def main():
    global app  # Make app global so it can be accessed by the quit action
    app = QApplication(sys.argv)
    
    # Don't quit when last window is closed (since we're a menu bar app)
    app.setQuitOnLastWindowClosed(False)
    
    menu = MeetingCoordinatorMenu()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()