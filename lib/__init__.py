# misc classes live here

import pygame



class Scheduler:
    def __init__(self):
        self.callbacks = {}
        self.next_event = pygame.USEREVENT

    def test(self, event):
        try:
            self.callbacks[event.type]()
        except KeyError:
            pass

    def schedule_interval(self, interval, callback):
        event = self.next_event
        self.callbacks[event] = callback
        pygame.time.set_timer(event, interval)
        pygame.event.set_allowed([event])
        self.next_event += 1
        return event
