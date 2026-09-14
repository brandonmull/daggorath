"""Frame observation — a change-by-change reader over MameOperator.

MameOperator.recv() returns every buffered change as a list of
(frame_number, state) pairs; a frame with no change is not reported, so the
gap between consecutive frame numbers is the record of the still frames. This
wrapper meters those changes out one at a time, so a caller watching a
command's window sees every change even when several arrive in one batch, and
carries the gap so the still frames stay visible.
"""


class FrameObservation:
    """A one-change-at-a-time view of the operator's reported changes.

    Lifecycle: built over a started MameOperator; the first change is read at
    construction. Status: shared observer for the command-latency sandbox.
    """

    def __init__(self, operator):
        self._operator = operator
        self._changes = []
        self._frame_number = None
        self._state = None
        self._gap = 0
        self.advance_to_next_change()

    @property
    def frame_number(self):
        """The frame number of the current change (None before the first)."""
        return self._frame_number

    @property
    def state(self):
        """The true state carried by the current change."""
        return self._state

    @property
    def gap(self):
        """Still frames between the previous change and the current one."""
        return self._gap

    def advance_to_next_change(self):
        """Serve the next buffered change, reading from the operator when empty."""
        while not self._changes:
            self._changes = self._operator.recv()
        previous_frame_number = self._frame_number
        self._frame_number, self._state = self._changes.pop(0)
        if previous_frame_number is None:
            self._gap = 0
        else:
            self._gap = self._frame_number - previous_frame_number
