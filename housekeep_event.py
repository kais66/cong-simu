from event import Event

class LogEvent(Event):
    def __init__(self, simu, timestamp, log_owner, periodicity):
        super(LogEvent, self).__init__(simu, timestamp)
        self._log_owner = log_owner
        self._periodicity = periodicity

    def execute(self):
        self._log_owner.log()

        evt = LogEvent(self._simu, self.timestamp() + self._periodicity,
                       self._log_owner, self._periodicity)
        self._simu.enqueue(evt)
