class ScriptedInput:
    def __init__(self, keys):
        self.keys = iter(keys)
        self.reads = 0

    def read_key(self):
        self.reads += 1
        try:
            return next(self.keys)
        except StopIteration:
            raise AssertionError("No scripted keys left; end the sequence with ':quit'") from None


class RecordingRenderer:
    def __init__(self):
        self.states = []
        self.events = []

    def start(self):
        self.events.append("start")

    def update_render(self, state):
        self.events.append("render")
        self.states.append(state)

    def close(self):
        self.events.append("close")
