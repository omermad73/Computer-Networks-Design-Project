from Event import Event

class Timeline:
    def __init__(self):
        self.events = []

    def do_event(self):
        '''do things'''
        self.remove_head()

    def add_event(self, event):
        if not isinstance(event, Event):
            raise ValueError("Only Event instances can be added to the timeline.")
        self.events.append(event)

    def remove_head(self):
        self.events.remove(0)

    def sort(self):
        self.events.sort(key=lambda event: event.scheduled_time)

    def __str__(self):
        return '\n'.join([f"Event ID: {event.id}, Scheduled Time: {event.scheduled_time}, Type: {event.event_type}" for event in self.events])
