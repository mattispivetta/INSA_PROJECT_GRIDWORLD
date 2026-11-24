class TerminalInput:
    def read_key(self) -> str | None:
        try:
            return input()
        except (EOFError, KeyboardInterrupt):
            return ":quit"
