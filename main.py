from datetime import datetime, timedelta
import pytz
import time
from config import load_config, setup_initial_config
from calendar_access import CalendarAccess, CalendarAccessError

class CalendarAccessError(Exception):
    """Custom exception for calendar access errors"""
    pass
    
def list_calendars():
    """List all available calendars"""
    try:
        calendar_access = CalendarAccess.get_instance()
        calendars = calendar_access.list_calendars()
        if not calendars:
            raise CalendarAccessError("No calendars found. Please ensure Calendar app is set up.")
        return calendars
    except Exception as e:
        raise CalendarAccessError(f"Failed to access calendars: {str(e)}")

def get_available_slots(calendar_name, target_date, working_hours, duration_minutes=60, target_tz=None):
    """Find available time slots for a given date"""
    # Set up timezone info
    local_tz = pytz.timezone('Asia/Jerusalem')  # Your local timezone
    target_pytz = pytz.timezone(target_tz) if target_tz else local_tz
    
    # Create datetime objects with timezone info
    date_str = target_date.strftime('%Y-%m-%d')
    day_start = local_tz.localize(datetime.strptime(f"{date_str} {working_hours['start']}", '%Y-%m-%d %H:%M'))
    day_end = local_tz.localize(datetime.strptime(f"{date_str} {working_hours['end']}", '%Y-%m-%d %H:%M'))
    
    # Convert working hours to target timezone if needed
    if target_tz:
        day_start = day_start.astimezone(target_pytz)
        day_end = day_end.astimezone(target_pytz)
    
    # Get busy periods using new calendar access
    try:
        calendar_access = CalendarAccess.get_instance()
        busy_periods = calendar_access.get_events_for_date(calendar_name, target_date)
        if busy_periods is None:
            return []
    except Exception as e:
        print(f"Error getting events: {str(e)}")
        return []
    
    # Add timezone info to event times and convert to target timezone
    target_events = []
    for start, end in busy_periods:
        # Add local timezone info to naive datetimes
        if start.tzinfo is None:
            start = local_tz.localize(start)
        if end.tzinfo is None:
            end = local_tz.localize(end)
            
        # Convert to target timezone if needed
        if target_tz:
            start = start.astimezone(target_pytz)
            end = end.astimezone(target_pytz)
            
        # Filter events for target date
        if start.date() == target_date.date():
            target_events.append((start, end))
    
    # Start with the full working day as one available slot
    available_slots = [(day_start, day_end)]
    
    # Remove busy periods from available slots
    for busy_start, busy_end in target_events:
        new_available_slots = []
        for avail_start, avail_end in available_slots:
            # If busy period overlaps with available slot
            if busy_start < avail_end and busy_end > avail_start:
                # Add time before busy period if there's enough time
                if busy_start > avail_start:
                    new_available_slots.append((avail_start, busy_start))
                # Add time after busy period if there's enough time
                if busy_end < avail_end:
                    new_available_slots.append((busy_end, avail_end))
            else:
                # No overlap, keep the slot as is
                new_available_slots.append((avail_start, avail_end))
        available_slots = new_available_slots
    
    # Filter slots that are too short for the desired duration
    duration = timedelta(minutes=duration_minutes)
    valid_slots = []
    for start, end in available_slots:
        slot_duration = end - start
        if slot_duration >= duration:
            valid_slots.append((start, end))
    
    return valid_slots

def format_slots_for_email(slots, timezone="Local Time"):
    """Format available slots into email-friendly text"""
    if not slots:
        return "No available slots found for this day."
    
    formatted_slots = []
    for start, end in slots:
        slot_str = f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        formatted_slots.append(slot_str)
    
    date_str = slots[0][0].strftime('%A, %B %d')
    return f"On {date_str}, I am available to meet in any of the following times:\n" + \
           f"{', '.join(formatted_slots)} ({timezone})"

def validate_calendar_config(config, available_calendars):
    """Validate that configured calendar exists, prompt for reconfiguration if needed"""
    if config['selected_calendar'] not in available_calendars:
        print(f"\nWarning: Previously configured calendar '{config['selected_calendar']}' is no longer available.")
        print("Available calendars have changed. Please select a new calendar.")
        return setup_initial_config(available_calendars)
    return config

def get_meeting_duration():
    """Ask user for desired meeting duration"""
    while True:
        try:
            duration = input("\nEnter desired meeting duration in minutes (e.g., 30, 60): ")
            duration = int(duration)
            if duration <= 0:
                print("Duration must be positive")
                continue
            if duration > 480:  # 8 hours
                print("Duration seems too long. Please enter a value less than 480 minutes (8 hours)")
                continue
            return duration
        except ValueError:
            print("Please enter a valid number")

def get_target_date():
    """Ask user for the target date"""
    while True:
        try:
            date_str = input("\nEnter target date (YYYY-MM-DD) or press Enter for today: ")
            if not date_str:
                return datetime.now()
            
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Prevent past dates
            if target_date.date() < datetime.now().date():
                print("Please enter a current or future date")
                continue
                
            return target_date
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format")

def get_location_timezone(location):
    """Convert a location name to a timezone using geopy and timezonefinder"""
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder

    try:
        # Initialize the geocoder with a unique user agent
        geolocator = Nominatim(user_agent="meeting_coordinator")
        tf = TimezoneFinder()

        # Get location coordinates
        location_data = geolocator.geocode(location)
        if location_data is None:
            return None

        # Get timezone from coordinates
        timezone_str = tf.timezone_at(lat=location_data.latitude, lng=location_data.longitude)
        return timezone_str
    except Exception:
        return None

def get_target_timezone():
    """Ask user for the target timezone using natural language"""
    while True:
        location = input("\nEnter location (e.g., 'London, UK', 'Tel Aviv') or press Enter for local time: ")
        if not location:
            return None

        if location.strip().lower() == 'local':
            return None
            
        # Try to get timezone from location
        timezone_str = get_location_timezone(location)
        if timezone_str:
            try:
                # Verify the timezone is valid
                pytz.timezone(timezone_str)
                return timezone_str
            except pytz.exceptions.UnknownTimeZoneError:
                pass
        
        print("Location not found. Please try another location or 'local' for local time.")
        continue

def get_target_dates():
    """Ask user for target dates"""
    dates = []
    while True:
        try:
            print("\nSelect dates to check:")
            print("1. Today")
            print("2. Tomorrow")
            print("3. Enter specific date")
            print("4. Done adding dates")
            
            choice = input("Choice (1-4): ")
            
            if choice == "1":
                dates.append(datetime.now())
                print("Added today")
            elif choice == "2":
                dates.append(datetime.now() + timedelta(days=1))
                print("Added tomorrow")
            elif choice == "3":
                date_str = input("Enter date (YYYY-MM-DD): ")
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                if target_date.date() < datetime.now().date():
                    print("Please enter a current or future date")
                    continue
                dates.append(target_date)
                print(f"Added {target_date.strftime('%Y-%m-%d')}")
            elif choice == "4":
                if not dates:
                    print("Please select at least one date")
                    continue
                return sorted(dates)
            else:
                print("Please enter 1, 2, 3, or 4")
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format")

def format_multiple_days_email(all_slots, timezone="Local Time"):
    """Format available slots for multiple days into a concise text"""
    if not all_slots:
        return "I don't have any availability during the requested dates."

    # Convert slots into a readable format
    available_days = []
    for date, slots in sorted(all_slots.items()):
        if slots:  # Only show dates that have available slots
            date_str = date.strftime('%A, %B %d')
            
            # Format the time ranges
            time_ranges = []
            for start, end in sorted(slots):
                time_ranges.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            
            # Combine all time ranges for this day
            times = ", ".join(time_ranges)
            available_days.append(f"On {date_str}, I am available to meet in any of the following times:\n{times}")
    
    if not available_days:
        return "I don't have any availability during the requested dates."

    # Construct the final string
    if len(available_days) == 1:
        result = available_days[0]
    else:
        *first_days, last_day = available_days
        result = ", ".join(first_days) + f".\nOtherwise, I am also available on {last_day}"

    # Add timezone if it's not local
    if timezone and timezone != "Local Time":
        result += f" ({timezone})"
    
    return result

def main():
    calendars = list_calendars()
    if not calendars:
        print("No calendars found!")
        return
    
    config = load_config()
    
    if config['selected_calendar'] is None:
        config = setup_initial_config(calendars)
    else:
        config = validate_calendar_config(config, calendars)
    
    print(f"\nUsing calendar: {config['selected_calendar']}")
    print(f"Working hours: {config['working_hours']['start']} - {config['working_hours']['end']}")
    
    # Get desired meeting duration
    duration = get_meeting_duration()
    
    # Get target dates
    target_dates = get_target_dates()
    
    # Get target timezone
    target_tz = get_target_timezone()
    
    print(f"\nLooking for {duration}-minute slots...")
    
    all_available_slots = {}
    for target_date in target_dates:
        print(f"\nChecking availability for {target_date.strftime('%Y-%m-%d')}...")
        available_slots = get_available_slots(
            config['selected_calendar'],
            target_date,
            config['working_hours'],
            duration,
            target_tz
        )
        all_available_slots[target_date.date()] = available_slots
    
    print("\nAvailable slots:")
    print(format_multiple_days_email(all_available_slots, target_tz))

if __name__ == "__main__":
    main()


    