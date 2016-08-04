import sys
import enum

class InvalidTestCaseError(Exception):
    pass

class TestTimeoutError(Exception):
    pass

class InterestingnessTest:
    @classmethod
    def get_test_options(cls, env):
        return dict()

    def __init__(self, test_cases, options):
        self.test_cases = test_cases
        self.options = options

    def check(self):
        raise NotImplementedError("Please use a custom interestingness test class!")

    def run(self):
        try:
            result = self.check()
        except TestTimeoutError:
            sys.exit(-1)
        except InvalidTestCaseError:
            sys.exit(-2)

        if result:
            sys.exit(0)
        else:
            sys.exit(1)
