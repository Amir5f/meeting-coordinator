from datetime import datetime
from Foundation import (
    NSDate, 
    NSCalendar, 
    NSCalendarUnitYear, 
    NSCalendarUnitMonth, 
    NSCalendarUnitDay,
    NSCalendarUnitHour,
    NSCalendarUnitMinute,
    NSCalendarUnitSecond
)
from EventKit import (
    EKEventStore, 
    EKSpan, 
    EKEntityMaskEvent, 
    EKEntityTypeEvent
)


class CalendarAccessError(Exception):
    """Custom exception for calendar access errors"""
    pass


class CalendarAccess:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure we only create one EKEventStore"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
            """Initialize EventKit store and request access"""
            import time
            self.store = EKEventStore.alloc().init()
            self.access_granted = False
            
            # Check current authorization status
            auth_status = EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent)
            
            if auth_status == 0:  # Not determined
                print("Requesting calendar access...")
                # Request access and wait for response
                self.store.requestAccessToEntityType_completion_(
                    EKEntityTypeEvent,
                    lambda granted, error: setattr(self, 'access_granted', granted)
                )
                
                # Wait for the permission dialog response
                for _ in range(10):  # Wait up to 10 seconds
                    if self.access_granted:
                        break
                    time.sleep(1)
                    
            elif auth_status == 3:  # Authorized
                self.access_granted = True
                print("Calendar access already granted")
            else:
                print("Calendar access denied. Please grant access in System Settings > Privacy & Security > Calendars")
    
    def list_calendars(self):
        """List all available calendars"""
        if not self.access_granted:
            raise CalendarAccessError("Calendar access not granted")
        
        return [cal.title() for cal in self.store.calendars()]
    
    def get_calendar_by_name(self, calendar_name):
        """Get a specific calendar by name"""
        if not self.access_granted:
            raise CalendarAccessError("Calendar access not granted")
            
        for calendar in self.store.calendars():
            if calendar.title() == calendar_name:
                return calendar
        return None
    
    def get_events_for_date(self, calendar_name, target_date):
        """Get events for a specific date
        
        Args:
            calendar_name (str): Name of the calendar to query
            target_date (datetime): The date to get events for
            
        Returns:
            list: List of (start_datetime, end_datetime) tuples
        """
        import time
        start_time = time.time()
        
        if not self.access_granted:
            raise CalendarAccessError("Calendar access not granted")
            
        # Get the calendar
        calendar = self.get_calendar_by_name(calendar_name)
        if not calendar:
            raise CalendarAccessError(f"Calendar '{calendar_name}' not found")
        
        # Create start and end dates for the query
        start_date = target_date.replace(hour=0, minute=0, second=0)
        start_date_ns = NSDate.dateWithTimeIntervalSince1970_(start_date.timestamp())
        
        end_date = target_date.replace(hour=23, minute=59, second=59)
        end_date_ns = NSDate.dateWithTimeIntervalSince1970_(end_date.timestamp())
        
        print(f"Calendar setup took: {time.time() - start_time:.2f} seconds")
        query_start = time.time()
        
        # Create the predicate for the query
        predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(
            start_date_ns,
            end_date_ns,
            [calendar]
        )
        
        # Fetch events
        events = self.store.eventsMatchingPredicate_(predicate)
        print(f"Event query took: {time.time() - query_start:.2f} seconds")
        
        # Filter and format results
        format_start = time.time()
        result = []
        for event in events:
            if not event.isAllDay():  # Skip all-day events
                start_ts = event.startDate().timeIntervalSince1970()
                end_ts = event.endDate().timeIntervalSince1970()
                start = datetime.fromtimestamp(start_ts)
                end = datetime.fromtimestamp(end_ts)
                result.append((start, end))
        
        print(f"Event formatting took: {time.time() - format_start:.2f} seconds")
        print(f"Total calendar query took: {time.time() - start_time:.2f} seconds")
        
        return result