class TypeAnalysisException(Exception):
    def __init__(self, value):
        self.value = value
        self.message = f"[FAIL] {value} "
        super().__init__(self.message)