#!/usr/bin/env python3

from enum import Enum
from interestingness_tests import base
from interestingness_tests import opencl
import os
import sys

class WrongCodeBugOpenCLInterestingnessTest(opencl.OpenCLInterestingnessTest):
    class OptimisationLevel(Enum):
        unoptimised = "unoptimised"
        optimised = "optimised"
        either = "either"
        all = "all"

    @staticmethod
    def __get_optimisation_level(level_str):
        if level_str is None:
            return WrongCodeBugOpenCLInterestingnessTest.OptimisationLevel.either

        if level_str == "optimised":
            return WrongCodeBugOpenCLInterestingnessTest.OptimisationLevel.optimised
        elif level_str == "unoptimised":
            return WrongCodeBugOpenCLInterestingnessTest.OptimisationLevel.unoptimised
        elif level_str == "either":
            return WrongCodeBugOpenCLInterestingnessTest.OptimisationLevel.either
        elif level_str == "all":
            return WrongCodeBugOpenCLInterestingnessTest.OptimisationLevel.all
        else:
            print("Invalid optimisation level!")
            sys.exit(1)

    @classmethod
    def get_test_options(cls, env):
        options = super().get_test_options(env)

        options["use_oracle"] = env.get("CREDUCE_TEST_USE_ORACLE")
        options["optimisation_level"] = env.get("CREDUCE_TEST_OPTIMISATION_LEVEL")
        options["check_static"] = env.get("CREDUCE_TEST_STATIC", False)

        return options

    def __init__(self, test_cases, options):
        super().__init__(test_cases, options)

        if "use_oracle" in self.options and self.options["use_oracle"] is not None:
            self.use_oracle = bool(int(self.options["use_oracle"]))
        else:
            self.use_oracle = True

        if "optimisation_level" in self.options:
            self.optimisation_level = self.__get_optimisation_level(self.options["optimisation_level"])
        else:
            self.optimisation_level = self.OptimisationLevel.either

        self.check_static = self.options["check_static"]

    def check(self):
        if self.check_static:
            if not self.is_valid_cl_launcher_test_case(self.test_case):
                raise base.InvalidTestCaseError("cl_launcher")

            if not self.is_statically_valid(self.test_case, self.timeout):
                raise base.InvalidTestCaseError("static")

        if self.use_oracle:
            # Implicitly checks if test case is valid in Oclgrind
            oracle = self.get_oracle_result(self.test_case, self.timeout)

            if oracle is None:
                raise base.InvalidTestCaseError("oracle")

            if self.optimisation_level is self.OptimisationLevel.optimised:
                proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

                if proc_opt is None or proc_opt.returncode != 0:
                    raise base.InvalidTestCaseError("optimised")

                return proc_opt.stdout != oracle
            elif self.optimisation_level is self.OptimisationLevel.unoptimised:
                proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

                if proc_unopt is None or proc_unopt.returncode != 0:
                    raise base.InvalidTestCaseError("unoptimised")

                return proc_unopt.stdout != oracle
            elif self.optimisation_level is self.OptimisationLevel.either:
                proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

                if proc_opt is None or proc_opt.returncode != 0:
                    raise base.InvalidTestCaseError("optimised")

                if proc_opt.stdout != oracle:
                    return True

                proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

                if proc_unopt is None or proc_unopt.returncode != 0:
                    raise base.InvalidTestCaseError("unoptimised")

                if proc_unopt.stdout != oracle:
                    return True

                return False
            elif self.optimisation_level is self.OptimisationLevel.all:
                proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

                if proc_opt is None or proc_opt.returncode != 0:
                    raise base.InvalidTestCaseError("optimised")

                if proc_opt.stdout == oracle:
                    return False

                proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

                if proc_unopt is None or proc_unopt.returncode != 0:
                    raise base.InvalidTestCaseError("unoptimised")

                if proc_unopt.stdout == oracle:
                    return False

                return True
        else:
            #FIXME: Need to run both?
            if (not self.is_valid_oclgrind(self.test_case, self.timeout, optimised=True) or
                not self.is_valid_oclgrind(self.test_case, self.timeout, optimised=False)):
                return False

            proc_opt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=True)

            if proc_opt is None or proc_opt.returncode != 0:
                raise base.InvalidTestCaseError("optimised")

            proc_unopt = self._run_cl_launcher(self.test_case, self.platform, self.device, self.timeout, optimised=False)

            if proc_unopt is None or proc_unopt.returncode != 0:
                raise base.InvalidTestCaseError("unoptimised")

            return proc_opt.stdout != proc_unopt.stdout

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_case = sys.argv[1]
    else:
        test_case = os.environ.get("CREDUCE_TEST_CASE")

    if (test_case is None or
        not os.path.isfile(test_case) or
        not os.access(test_case, os.F_OK)):
        print("Test case '{}' does not exist!".format(test_case)
              if test_case else
              "No test case! Set $CREDUCE_TEST_CASE or pass as argument")
        sys.exit(1)

    options = WrongCodeBugOpenCLInterestingnessTest.get_test_options(os.environ)

    test = WrongCodeBugOpenCLInterestingnessTest([test_case], options)
    test.run()
