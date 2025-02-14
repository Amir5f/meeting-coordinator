import sys
import os
import json
import re
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSystemTrayIcon, 
    QMenu, QAction, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QSpinBox, QDateEdit, 
    QComboBox, QMessageBox, QGroupBox, QGridLayout, QCheckBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from datetime import datetime, timedelta
from config import load_config, setup_initial_config
import pytz
from main import (list_calendars, get_available_slots, format_multiple_days_email, get_location_timezone,
                 CalendarAccessError)


class SettingsWindow(QWidget):
    def __init__(self, current_config, menu_instance):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
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
        calendar_layout.setContentsMargins(10, 10, 10, 10)

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
        
        self.setMinimumWidth(450)  

        
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
    min-height: 80px;
    max-height: 400px;
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
    def setup_window(self):
        self.window = CheckAvailabilityWindow()

    def __init__(self):
        super().__init__()
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        self.window = None
        self.config = load_config()
        if self.config is None:
            self.config = setup_initial_config(list_calendars())
        
        # Set icon
        resources_path = os.path.join(os.path.dirname(__file__), 'resources')
        icon_path = os.path.join(resources_path, 'icon_64x64.png')
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            icon_pixmap = QPixmap(64, 64)
            icon_pixmap.fill(Qt.transparent)
            painter = QPainter(icon_pixmap)
            painter.setBrush(QColor('#0078D4'))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(8, 8, 48, 48)
            painter.end()
            self.setIcon(QIcon(icon_pixmap))
        
        self.setup_menu()
        self.setup_window()
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
        check_action_icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'calendar-search.png')        
        check_action = QAction("Check Availability", self)
        check_action.setIcon(QIcon(check_action_icon_path))
        check_action.triggered.connect(self.show_window)
        self.menu.addAction(check_action)
        
        self.menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action_icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'settings.png')
        settings_action.setIcon(QIcon(settings_action_icon_path))
        settings_action.triggered.connect(self.show_settings)
        self.menu.addAction(settings_action)
        
        about_action = QAction("About", self)
        about_action_icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon_64x64.png')
        about_action.setIcon(QIcon(about_action_icon_path))
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)

        self.menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action_icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'log-out.png')
        quit_action.setIcon(QIcon(quit_action_icon_path))
        quit_action.triggered.connect(app.quit)
        self.menu.addAction(quit_action)
        
    def show_settings(self):
        self.config = load_config()  # Ensure we have latest config
        print(f"Opening settings with config: {self.config}")  # Debug
        self.settings_window = SettingsWindow(self.config, self)  # Pass self (the menu instance)
        self.settings_window.show()

    def show_about(self):
        self.about_window = AboutWindow()
        self.about_window.show()

    def show_window(self):
        # Create new window instance if needed
        if not hasattr(self, 'window') or not self.window:
            self.window = CheckAvailabilityWindow()
        
        geometry = self.geometry()
        window_x = geometry.x() - (self.window.width() // 2)
        window_y = 25
        
        screen = QApplication.primaryScreen().geometry()
        window_x = max(0, min(window_x, screen.width() - self.window.width()))
        
        self.window.move(window_x, window_y)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def delete_show_window(self):
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
        
        # Load last location if it exists
        if self.config.get('last_location'):
            self.location_input.setText(self.config['last_location'])        
        
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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Calendar selection
        calendar_group = QGroupBox("Calendar")
        calendar_layout = QHBoxLayout()
        calendar_layout.setContentsMargins(10, 10, 10, 10)        
        calendar_label = QLabel("Calendar:")
        self.calendar_combo = QComboBox()
        # Check if we have any calendars at all
        if not self.available_calendars:
            QMessageBox.critical(
                self,
                "No Calendars Available",
                "No calendars were found. Please check your Calendar app settings."
            )
            # Set a dummy item so the UI doesn't crash
            self.calendar_combo.addItem("No calendars available")
        else:
            self.calendar_combo.addItems(self.available_calendars)
            # Handle case where saved calendar is no longer available
            try:
                current_cal_index = self.available_calendars.index(self.config['selected_calendar'])
                self.calendar_combo.setCurrentIndex(current_cal_index)
            except ValueError:
                # If saved calendar not found, show error and default to first available
                self.calendar_combo.setCurrentIndex(0)
                # Update the config with the new calendar
                previous_calendar = self.config['selected_calendar']
                self.config['selected_calendar'] = self.available_calendars[0]
                from config import save_config
                save_config(self.config)
                
                QMessageBox.warning(
                    self,
                    "Calendar Not Found",
                    f"Previously selected calendar '{previous_calendar}' is no longer available.\n"
                    f"Defaulting to '{self.available_calendars[0]}'.\n\n"
                    "You can select a different calendar from the dropdown."
                )
        
        calendar_layout.addWidget(calendar_label)
        calendar_layout.addWidget(self.calendar_combo)
        layout.addLayout(calendar_layout)

        # Working Hours Group
        hours_group = QGroupBox("Working Hours")
        hours_layout = QGridLayout()
        hours_layout.setContentsMargins(10, 10, 10, 10)  
        hours_layout.setVerticalSpacing(10)
        
        # Time inputs - always enabled and pre-populated with default hours
        hours_layout.addWidget(QLabel("Start:"), 0, 0)
        self.temp_start_time = QLineEdit(self.config['working_hours']['start'])
        self.temp_start_time.setMinimumWidth(100)
        self.temp_start_time.setMinimumHeight(32)
        hours_layout.addWidget(self.temp_start_time, 0, 1)
        
        hours_layout.addWidget(QLabel("End:"), 1, 0)
        self.temp_end_time = QLineEdit(self.config['working_hours']['end'])
        self.temp_end_time.setMinimumWidth(100)
        self.temp_end_time.setMinimumHeight(32)
        hours_layout.addWidget(self.temp_end_time, 1, 1)
        
        # Save as default checkbox
        self.save_default_checkbox = QCheckBox("Save as default hours")
        hours_layout.addWidget(self.save_default_checkbox, 2, 0, 1, 2)        
        
        hours_group.setLayout(hours_layout)
        layout.addWidget(hours_group)

        # Date selection
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setMinimumDate(QDate.currentDate())
        date_edit.setMinimumHeight(32)
        self.dates_group = QGroupBox("Select Dates")
        self.dates_layout = QVBoxLayout()
        
        # Initial date field
        self.add_date_field()
        
        # Add date button
        add_date_button = QPushButton("+ Add Date")
        add_date_button.clicked.connect(self.add_date_field)
        self.dates_layout.addWidget(add_date_button)
        
        self.dates_group.setLayout(self.dates_layout)
        self.dates_group.setContentsMargins(10, 10, 10, 10)
        self.dates_layout.setSpacing(10)
        layout.addWidget(self.dates_group)
        
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
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Available time slots will appear here...")
        self.results_text.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        self.results_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Copy button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_button)
        
        self.setMinimumWidth(400)

    def add_date_field(self):
        date_row = QHBoxLayout()
        
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setMinimumDate(QDate.currentDate())
        date_edit.setMinimumHeight(32)
        self.date_widgets.append(date_edit)
        
        remove_button = QPushButton("×")
        remove_button.setMaximumWidth(30)
        remove_button.clicked.connect(lambda: self.remove_date_field(date_row, date_edit))
        
        date_row.addWidget(date_edit)
        date_row.addWidget(remove_button)
        
        # Insert before the add button
        self.dates_layout.insertLayout(self.dates_layout.count() - 1, date_row)

    def remove_date_field(self, date_row, date_edit):
        if len(self.date_widgets) > 1:
            self.date_widgets.remove(date_edit)
            while date_row.count():
                item = date_row.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            date_row.deleteLater()


    def get_working_hours(self):
        """Get current working hours and optionally save as default"""
        start = self.temp_start_time.text().strip()
        end = self.temp_end_time.text().strip()
        
        time_format = "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not (re.match(time_format, start) and re.match(time_format, end)):
            QMessageBox.warning(self, "Invalid Time Format", 
                            "Please enter times in HH:MM format (e.g., 09:00)")
            return None
        
        working_hours = {'start': start, 'end': end}
        
        # If save as default is checked, update the config
        if self.save_default_checkbox.isChecked():
            self.config['working_hours'] = working_hours.copy()
            from config import save_config
            save_config(self.config)
            self.save_default_checkbox.setChecked(False)  # Reset checkbox after saving
        
        return working_hours
    
    def check_availability(self):
        self.results_text.clear()
        # Disable the check button while processing
        check_button = self.sender()
        if check_button:
            check_button.setEnabled(False)
        
        # Set wait cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            total_start = time.time() # Debug
            print(f"\n=== Performance Log ===") # Debug
            cal_start = time.time() # Debug

            try:
                available_calendars = list_calendars()
                current_calendar = self.calendar_combo.currentText()
                print(f"Calendar check took: {time.time() - cal_start:.2f} seconds")
                
                if current_calendar not in available_calendars:
                    response = QMessageBox.warning(
                        self,
                        "Calendar Not Available",
                        f"The selected calendar '{current_calendar}' is no longer available.\n\n"
                        "Would you like to select a different calendar?",
                        QMessageBox.Yes | QMessageBox.Cancel
                    )
                    
                    if response == QMessageBox.Yes:
                        # Update calendar combo box
                        self.calendar_combo.clear()
                        self.calendar_combo.addItems(available_calendars)
                        
                        # Show calendar selection dialog
                        calendar_dialog = QMessageBox(self)
                        calendar_dialog.setIcon(QMessageBox.Question)
                        calendar_dialog.setWindowTitle("Select Calendar")
                        calendar_dialog.setText("Please select a calendar from the dropdown and try again.")
                        calendar_dialog.exec_()
                    return
                
            except Exception as calendar_error:
                QMessageBox.critical(
                    self,
                    "Calendar Access Error",
                    str(calendar_error)
                )
                return
            
            # Get working hours
            hours_start = time.time()            # Debug
            working_hours = self.get_working_hours()
            print(f"Working hours check took: {time.time() - hours_start:.2f} seconds")
            if working_hours is None:
                return

            # Get selected calendar
            selected_calendar = self.calendar_combo.currentText() # Debug
            
            # Get selected dates
            dates_start = time.time()             # Debug
            selected_dates = []
            for date_widget in self.date_widgets:
                qdate = date_widget.date()
                date = datetime(qdate.year(), qdate.month(), qdate.day())
                selected_dates.append(date)
            print(f"Date processing took: {time.time() - dates_start:.2f} seconds") # Debug


            # Get duration
            duration = self.duration_input.value()
            
            # Get location and timezone
            loc_start = time.time()            
            location = self.location_input.text()
            timezone_str = None
            if location:
                # Save the location to config
                self.config['last_location'] = location
                from config import save_config
                save_config(self.config)

                timezone_str = get_location_timezone(location)
                if not timezone_str:
                    self.results_text.setText("Could not determine timezone for the given location.")
                    return
            print(f"Location/timezone processing took: {time.time() - loc_start:.2f} seconds")# Debug
            
            # Process availability
            slots_start = time.time() # Debug            
            all_available_slots = {}
            for target_date in selected_dates:
                print(f"\nProcessing date: {target_date.strftime('%Y-%m-%d')}") # Debug
                event_fetch_start = time.time() # Debug
                available_slots = get_available_slots(
                    selected_calendar,
                    target_date,
                    working_hours,
                    duration,
                    timezone_str
                )
                print(f"Event fetch and slot calculation took: {time.time() - event_fetch_start:.2f} seconds") # Debug
                all_available_slots[target_date.date()] = available_slots
            print(f"Total slots processing took: {time.time() - slots_start:.2f} seconds")# Debug

            
            # Format and display results
            format_start = time.time()            # Debug
            results = format_multiple_days_email(all_available_slots, timezone_str)
            self.results_text.setText(results)
            print(f"Results formatting took: {time.time() - format_start:.2f} seconds")# Debug
            
            print(f"\nTotal execution time: {time.time() - total_start:.2f} seconds")
            print("===================\n")

        except Exception as e:
            self.results_text.setText(f"An error occurred: {str(e)}")
        finally:
            # Restore cursor
            QApplication.restoreOverrideCursor()
            # Re-enable the check button
            if check_button:
                check_button.setEnabled(True)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.results_text.toPlainText())

class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About Meeting Coordinator")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #E5E5E5;
            }
            QLabel {
                color: #000000;
                background-color: #E5E5E5;
            }
        """)        

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon_128x128.png')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        title = QLabel("Meeting Coordinator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; background-color: #E5E5E5;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("Version: 0.7")
        version.setStyleSheet("color: #666;")
        layout.addWidget(version)
        
        copyright = QLabel("Copyright © 2025 Amir Fischer. All rights reserved.")
        copyright.setWordWrap(True)
        layout.addWidget(copyright)
        
        self.setFixedSize(300, 280)

def main():
    global app  # Make app global so it can be accessed by the quit action
    app = QApplication(sys.argv)
    
    # Don't quit when last window is closed (since we're a menu bar app)
    app.setQuitOnLastWindowClosed(False)

    # Set application-wide icon
    app_icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon_64x64.png')

    
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
    else:
        print(f"Warning: Icon file not found at {app_icon_path}")
    
    menu = MeetingCoordinatorMenu()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()