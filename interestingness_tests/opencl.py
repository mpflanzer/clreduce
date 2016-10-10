from interestingness_tests import base
import os
import platform
import re
import subprocess

class OpenCLInterestingnessTest(base.InterestingnessTest):
    @classmethod
    def get_test_options(cls, env):
        options = super().get_test_options(env)

        options["cl_launcher"] = env.get("CREDUCE_TEST_CL_LAUNCHER")
        options["clang"] = env.get("CREDUCE_TEST_CLANG")
        options["libclc_include_path"] = env.get("CREDUCE_LIBCLC_INCLUDE_PATH")
        options["platform"] = env.get("CREDUCE_TEST_PLATFORM")
        options["device"] = env.get("CREDUCE_TEST_DEVICE")
        options["timeout"] = env.get("CREDUCE_TEST_TIMEOUT")
        options["conservative"] = env.get("CREDUCE_TEST_CONSERVATIVE")

        return options

    def __init__(self, test_cases, options):
        super().__init__(test_cases, options)

        if len(self.test_cases) > 0:
            self.test_case = self.test_cases[0]

        if "timeout" in self.options and self.options["timeout"] is not None:
            self.timeout = int(self.options["timeout"])
        else:
            self.timeout = 300

        if "clang" in self.options and self.options["clang"] is not None:
            self.clang = str(self.options["clang"])
        else:
            self.clang = "clang"

        if "cl_launcher" in self.options and self.options["cl_launcher"] is not None:
            self.cl_launcher = str(self.options["cl_launcher"])
        else:
            self.cl_launcher = "cl_launcher"

        if "libclc_include_path" in self.options and self.options["libclc_include_path"] is not None:
            self.libclc_include_path = str(self.options["libclc_include_path"])
        else:
            self.libclc_include_path = None

        if "platform" in self.options and self.options["platform"] is not None:
            self.platform = int(self.options["platform"])
        else:
            self.platform = 0

        if "device" in self.options and self.options["device"] is not None:
            self.device = int(self.options["device"])
        else:
            self.device = 0

        if "conservative" in self.options and self.options["conservative"] is not None:
            self.conservative = bool(int(self.options["conservative"]))
        else:
            self.conservative = True

    def _run_clang(self, test_case, timeout, extra_args=None):
        cmd = [self.clang]
        cmd.extend(["-x", "cl", "-fno-builtin", "-include", "clc/clc.h", "-Dcl_clang_storage_class_specifiers", "-g", "-c", "-Wall", "-Wextra", "-pedantic", "-Wconditional-uninitialized", "-Weverything", "-Wno-reserved-id-macro", "-fno-caret-diagnostics", "-fno-diagnostics-fixit-info", "-O1"])

        if self.libclc_include_path is not None:
            cmd.extend(["-I", self.libclc_include_path])

        if extra_args is not None:
            cmd.extend(extra_args)

        cmd.append(test_case)

        try:
            return subprocess.run(cmd, universal_newlines=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            raise base.TestTimeoutError("clang")
        except subprocess.SubprocessError:
            return None

    def _run_csa(self, test_case, timeout):
        #TODO: Maybe use scan-build?!
        #csa_args = ["-Xclang", "-analyze", "-Xclang", "-analyzer-checker", "-Xclang", "alpha,core,security,unix"]
        csa_args = ["--analyze", "-Xclang", "-analyzer-checker", "-Xclang", "alpha,core,security,unix"]

        try:
            return self._run_clang(test_case, timeout, csa_args)
        except base.TestTimeoutError:
            raise base.TestTimeoutError("clang static analyzer")

    def _run_oclgrind(self, test_case, timeout, optimised):
        cmd = ["oclgrind"]
        cmd.extend(["-Wall", "--uninitialized", "--arithmetic-exceptions", "--data-races", "--uniform-writes", "--stop-errors", "1"])
        cmd.append(self.cl_launcher)
        cmd.extend(["-p", "0", "-d", "0", "-f", test_case])

        if not optimised:
            cmd.append("---disable_opts")

        try:
            return subprocess.run(cmd, universal_newlines=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            raise base.TestTimeoutError("oclgrind")
        except subprocess.SubprocessError:
            return None

    def _run_cl_launcher(self, test_case, platform, device, timeout, optimised):
        cmd = [self.cl_launcher]
        cmd.extend(["-p", str(platform), "-d", str(device), "-f", test_case])

        if not optimised:
            cmd.append("---disable_opts")

        try:
            return subprocess.run(cmd, universal_newlines=True, timeout=timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            raise base.TestTimeoutError("cl_launcher")
        except subprocess.SubprocessError:
            return None

    def is_valid_result_access(self, test_case):
        with open(test_case, "r") as test_file:
            content = test_file.read()

        m = re.search(r"result\s*\[", content)

        if m is None:
            return True

        m = re.search(r"result\s*\[\s*get_linear_global_id\s*\(\s*\)\s*\]", content)

        if m is None:
            return False

        return True

    def is_valid_ast(self, test_case, timeout):
        try:
            proc = self._run_clang(test_case, timeout, ["-Xclang", "-ast-dump"])
        except base.TestTimeoutError:
            raise base.TestTimeoutError("clang ast")

        if proc is None or proc.returncode != 0:
            return False

        if (r"PointerToIntegral" not in proc.stdout):
            return True

        return False

    def is_valid_clang(self, test_case, timeout):
        proc = self._run_clang(test_case, timeout)

        if proc is None or proc.returncode != 0:
            return False

        if (r"warning: empty struct is a GNU extension" not in proc.stderr and
            r"warning: use of GNU empty initializer extension" not in proc.stderr and
            r"warning: incompatible pointer to integer conversion" not in proc.stderr and
            r"warning: incompatible integer to pointer conversion" not in proc.stderr and
            r"warning: incompatible pointer types initializing" not in proc.stderr and
            r"warning: comparison between pointer and integer" not in proc.stderr and
            r"warning: ordered comparison between pointer and integer" not in proc.stderr and
            r"warning: ordered comparison between pointer and zero" not in proc.stderr and
            r"is uninitialized when used within its own initialization [-Wuninitialized]" not in proc.stderr and
            r"is uninitialized when used here [-Wuninitialized]" not in proc.stderr and
            r"may be uninitialized when used here [-Wconditional-uninitialized]" not in proc.stderr and
            r"warning: use of GNU ?: conditional expression extension, omitting middle operand" not in proc.stderr and
            r"warning: control may reach end of non-void function [-Wreturn-type]" not in proc.stderr and
            r"warning: control reaches end of non-void function [-Wreturn-type]" not in proc.stderr and
            r"warning: zero size arrays are an extension [-Wzero-length-array]" not in proc.stderr and
            r"excess elements in " not in proc.stderr and
            r"warning: address of stack memory associated with local variable" not in proc.stderr and
            r"warning: type specifier missing" not in proc.stderr and
            r"warning: expected ';' at end of declaration list" not in proc.stderr and
            r" declaration specifier [-Wduplicate-decl-specifier]" not in proc.stderr):
            return True

        return False

    def is_valid_csa(self, test_case, timeout):
        proc = self._run_csa(test_case, timeout)

        if proc is None or proc.returncode != 0:
            return False

        if ("warning: Assigned value is garbage or undefined" not in proc.stderr and
            "warning: Undefined or garbage value returned to caller" not in proc.stderr and
            "is a garbage value" not in proc.stderr and
            "warning: Function call argument is an uninitialized value" not in proc.stderr and
            "warning: Dereference of null pointer" not in proc.stderr and
            "warning: Array subscript is undefined" not in proc.stderr and
            "results in a dereference of a null pointer" not in proc.stderr):
            return True

        return False

    def is_valid_cl_launcher_test_case(self, test_case):
        with open(test_case, "r") as test_file:
            content = test_file.read()

        # Make sure comment with dimensions is preserved
        m = re.match(r"//.* -g [0-9]+,[0-9]+,[0-9]+ -l [0-9]+,[0-9]+,[0-9]+", content)

        if m is None:
            return False

        # Early bailout if we trust Oclgrind to catch all problems
        if not self.conservative:
            return True

        # Access to result only with get_linear_global_id()
        if not self.is_valid_result_access(test_case):
            return False

        # Must not change get_linear_global_id
        m = re.search(r"return\s*\(\s*get_global_id\s*\(\s*2\s*\)\s*\*\s*get_global_size\s*\(\s*1\s*\)\s*\+\s*get_global_id\s*\(\s*1\s*\)\s*\)\s*\*\s*get_global_size\s*\(\s*0\s*\)\s*\+\s*get_global_id\s*\(\s*0\s*\)\s*;", content)

        if m is None:
            return False

        return True

    def is_statically_valid(self, test_case, timeout):
        if not self.is_valid_ast(test_case, timeout):
            return False

        # Run static analysis of the program
        # Better support for uninitialised values
        if not self.is_valid_clang(test_case, timeout):
            return False

        if not self.is_valid_csa(test_case, timeout):
            return False

        return True

    def is_valid_oclgrind(self, test_case, timeout, optimised):
        #TODO: Necessary to run both?
        proc = self._run_oclgrind(test_case, timeout, optimised)

        if proc is None or proc.returncode != 0:
            return False

        return True

    def get_oracle_result(self, test_case, timeout):
        proc_opt = self._run_oclgrind(test_case, timeout, optimised=True)

        if proc_opt is None or proc_opt.returncode != 0:
            return None

        proc_unopt = self._run_oclgrind(test_case, timeout, optimised=False)

        if proc_unopt is None or proc_unopt.returncode != 0:
            return None

        # Check for error in Oclgrind/Clang
        if proc_opt.stdout != proc_unopt.stdout:
            return None

        return proc_opt.stdout

    def is_valid_cl_launcher(self, test_case, platform, device, timeout, optimised):
        proc = self._run_cl_launcher(test_case, platform, device, timeout, optimised)

        if proc is None or proc.returncode != 0:
            return False

        return True
