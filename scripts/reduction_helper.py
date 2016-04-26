#!/usr/bin/env python3

import argparse
import atexit
import fileinput
import interestingness_tests
from interestingness_tests.wrong_code_bug import WrongCodeBugOpenCLInterestingnessTest
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import work_size_reduction

def which(cmd):
    if os.path.isfile(cmd) and os.access(cmd, os.F_OK):
        return cmd

    for path in os.environ["PATH"].split(os.pathsep):
        compound_path = os.path.join(path, cmd)

        if os.path.isfile(compound_path) and os.access(compound_path, os.F_OK):
            return compound_path
        else:
            compound_path += ".exe"

            if os.path.isfile(compound_path) and os.access(compound_path, os.F_OK):
                return compound_path

    return None

def remove_preprocessor_comments(test_case_name):
    for line in fileinput.input(test_case_name, inplace=True):
        if re.match(r'^# \d+ "[^"]*"', line):
            continue

        print(line, end="")

def get_test_class(test_str):
    if test_str is None:
        print("Missing --test argument")
        sys.exit(1)

    if test_str == "wrong-code-bug":
        return WrongCodeBugOpenCLInterestingnessTest
    else:
        print("Unknown interestingness test")
        sys.exit(1)

def get_test_script_file(test_str):
    if test_str is None:
        print("Missing --test argument")
        sys.exit(1)

    if test_str == "wrong-code-bug":
        return interestingness_tests.wrong_code_bug.__file__
    else:
        print("Unknown interestingness test")
        sys.exit(1)

def print_runtime(time_start):
    time_stop = time.monotonic()

    print("Runtime: {} seconds".format(round((time_stop - time_start))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to manage the reduction process of OpenCL test cases from generation to the reduced output.")
    inputGroup = parser.add_mutually_exclusive_group(required=True)
    inputGroup.add_argument("--generate", type=int, metavar="NUM", help="Generate NUM test cases on the fly")
    inputGroup.add_argument("--test-case-dir", dest="test_case_dir", help="OpenCL test case directory")
    inputGroup.add_argument("--test-cases", metavar="TEST CASE", dest="test_cases", nargs="+", help="OpenCL test case files")

    parser.add_argument("--exclude-file", dest="exclude_file", help="File containing a list of test cases that should be ignored")
    parser.add_argument("-n", metavar="NUM", type=int, help="Number of parallel interestingness tests per test case")

    processGroup = parser.add_mutually_exclusive_group()
    processGroup.add_argument("--preprocess", action="store_true", help="Preprocess test cases")
    processGroup.add_argument("--preprocessed", action="store_true", help="Treat test cases as already preprocessed")

    parser.add_argument("--check", action="store_true", help="Check whether the test cases are interesting")

    reduceGroup = parser.add_mutually_exclusive_group()
    reduceGroup.add_argument("--reduce-work-sizes-checked", dest="reduce_work_sizes", action="store_const", const=1, help="Reduce dimensions of the test cases")
    reduceGroup.add_argument("--reduce-work-sizes-unchecked", dest="reduce_work_sizes", action="store_const", const=2, help="Reduce dimensions of the test cases (unchecked)")

    parser.add_argument("--reduce", action="store_true", help="Start reduction of the test cases")
    parser.add_argument("--test", action="store", choices=["wrong-code-bug"], default=None, help="Interestingness test that should be used")
    parser.add_argument("--modes", nargs="+", action="store", choices=["atomic_reductions", "atomics", "barriers", "divergence", "fake_divergence", "group_divergence", "inter_thread_comm", "vectors"], help="CLsmith modes")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--log", help="Log completed test cases")

    args = parser.parse_args()

    # Print invocation for logging purposes
    print("Command: {}".format(" ".join(sys.argv)))

    # Track runtime
    time_start = time.monotonic()
    atexit.register(print_runtime, time_start)

    if args.generate or args.preprocess or not args.preprocessed:
        cl_smith_path = os.environ.get("CLSMITH_PATH")

        if cl_smith_path is None:
            print("CLSMITH_PATH not defined!")
            sys.exit(1)

    if args.check or args.reduce_work_sizes == 1 or args.reduce:
        if os.environ.get("CREDUCE_TEST_PLATFORM") is None:
            print("CREDUCE_TEST_PLATFORM not defined!")
            sys.exit(1)

        if os.environ.get("CREDUCE_TEST_DEVICE") is None:
            print("CREDUCE_TEST_DEVICE not defined!")
            sys.exit(1)

    if args.check or args.reduce_work_sizes == 1 or args.reduce:
        cl_launcher = os.environ.get("CREDUCE_TEST_CL_LAUNCHER", os.path.abspath("./cl_launcher"))

        if which(cl_launcher) is None:
            cl_launcher = os.path.basename(cl_launcher)

            if which(cl_launcher) is None:
                print("CREDUCE_TEST_CL_LAUNCHER not defined and cl_launcher not found!")
                sys.exit(1)

    clang = os.environ.get("CREDUCE_TEST_CLANG", os.path.abspath("./clang"))

    if which(clang) is None:
        clang = os.path.basename(clang)

        if which(clang) is None:
            print("CREDUCE_TEST_CLANG not defined and clang not found!")
            sys.exit(1)

    if args.reduce:
        if platform.system() == "Windows":
            if os.environ.get("CREDUCE_TEST_OCLGRIND_PLATFORM") is None:
                print("CREDUCE_TEST_OCLGRIND_PLATFORM not defined!")
                sys.exit(1)

            if os.environ.get("CREDUCE_TEST_OCLGRIND_DEVICE") is None:
                print("CREDUCE_TEST_OCLGRIND_DEVICE not defined!")
                sys.exit(1)

    # Save current directory
    orig_dir = os.getcwd()

    # Create output directory
    if args.output is None:
        output_dir = os.path.abspath(tempfile.mkdtemp(prefix="test_cases.", dir="."))
    else:
        output_dir = os.path.abspath(args.output)

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

    # Get excluded files
    excluded_files = [];

    if args.exclude_file and os.path.exists(args.exclude_file):
        with open(args.excludeFile, "r") as f:
            excluded_files.extend(f.read().splitlines())

    # Get test case filenames
    if args.generate:
        test_cases = [os.path.join(output_dir, "CLProg_{}.cl".format(i)) for i in range(0, args.generate)]
        test_case_count = args.generate
        cl_smith_tool = os.path.join(cl_smith_path, "CLSmith")
    elif args.test_cases:
        test_cases = [os.path.join(orig_dir, test_case) for test_case in args.test_cases if os.path.basename(test_case) not in excluded_files]
        test_case_count = len(test_cases)
    elif args.test_case_dir:
        test_case_dir = os.path.join(orig_dir, args.test_case_dir)
        p = pathlib.Path(test_case_dir)
        test_cases = [str(test_case) for test_case in p.glob("*.cl") if test_case.name not in excluded_files]
        test_case_count = len(test_cases)

    # Sort test cases
    alpha_num_key = lambda s : [int(c) if c.isdigit() else c for c in re.split("([0-9]+)", s)]
    test_cases.sort(key=alpha_num_key)

    # Log completed test cases
    if args.log:
        log_file = open(os.path.abspath(args.log), "a", 1)

    # Change to output directory
    os.chdir(output_dir)

    # Copy header files if unpreprocessed test cases should be reduced etc.
    if not args.preprocess and not args.preprocessed:
        shutil.copy(os.path.join(cl_smith_path, "CLSmith.h"), ".")
        shutil.copy(os.path.join(cl_smith_path, "safe_math_macros.h"), ".")
        shutil.copy(os.path.join(cl_smith_path, "cl_safe_math_macros.h"), ".")

    # Iterate over all test cases
    for test_case in test_cases:
        test_case_file = test_case
        test_case_name = os.path.basename(test_case_file)
        test_case_dir = os.path.dirname(test_case_file)

        print("")
        print(test_case_name, end=" ", flush=True)

        # Generate test case if desired
        if args.generate:
            try:
                cmd = [cl_smith_tool]

                if args.modes:
                    cmd.extend(["--" + mode for mode in args.modes])

                subprocess.run(cmd, timeout=60, check=True)
            except subprocess.CalledProcessError:
                print("-> aborted generation")
                continue

            shutil.move("CLProg.c", test_case_file)

            if args.verbose:
                print("-> generated", end=" ", flush=True)

        # Preprocess test case if desired or copy original test case
        if args.preprocess:
            try:
                cmd = [clang]
                cmd.extend(["-I", cl_smith_path, "-E", "-CC", "-o", "_{}".format(test_case_name), test_case_file])
                subprocess.run(cmd, timeout=60, check=True)
                remove_preprocessor_comments("_{}".format(test_case_name))
                shutil.move("_{}".format(test_case_name), test_case_name)
                test_case_file = test_case_name

                if args.verbose:
                    print("-> preprocessed", end=" ", flush=True)
            except subprocess.CalledProcessError:
                print("-> aborted preprocessing", end=" ", flush=True)
                continue
        else:
            if not os.path.samefile(output_dir, test_case_dir):
                shutil.copy(test_case_file, test_case_name)
                test_case_file = test_case_name

        # Check if test case is interesting
        if args.check:
            test_class = get_test_class(args.test)
            options = test_class.get_test_options(os.environ)
            test = test_class([test_case_file], options)
            result = test.check()

            if not result:
                os.unlink(test_case_file)
                print("-> check failed", end=" ", flush=True)
                continue
            else:
                if args.verbose:
                    print("-> check succeeded", end=" ", flush=True)

        # Reduce work sizes of the test case
        if args.reduce_work_sizes:
            options = get_test_options(os.environ)
            test = args.test(test_case_file, options)
            reducer = work_size_reduction.WorkSizeReducer(test_case_file, test)
            success = reducer.run(checked=(args.reduce_work_sizes == 1))

            if not result:
                if args.verbose:
                    print("-> work sizes unchanged", end=" ", flush=True)
            else:
                if args.verbose:
                    print("-> work sizes reduced", end=" ", flush=True)

        if args.reduce:
            reduction_env = os.environ
            reduction_env["CREDUCE_TEST_CASE"] = test_case_file

            test_script_file = get_test_script_file(args.test)

            # Create test case wrapper
            #FIXME: Call python script directly?
            if platform.system() == "Windows":
                test_wrapper = "test_wrapper.bat"

                with open(test_wrapper, "w") as test_file:
                    test_file.write("python {}\n".format(test_script_file))

                os.chmod(test_wrapper, 0o744)
            else:
                test_wrapper = "test_wrapper.sh"

                with open(test_wrapper, "w") as test_file:
                    test_file.write("#!/bin/bash\n")
                    test_file.write("exec python {}\n".format(test_script_file))

                os.chmod(test_wrapper, 0o744)

            cmd = ["perl"]
            cmd.extend(["--", which("creduce")])

            if args.n:
                cmd.extend(["--n", str(args.n)])

            if args.verbose:
                cmd.append("--debug")

            cmd.append(test_wrapper)
            cmd.append(test_case_file)

            try:
                subprocess.check_call(cmd, env=reduction_env, timeout=timeout)
            except subprocess.SubprocessError:
                print("-> reduction aborted", end=" ", flush=True)

        print("-> done", end=" ", flush=True)

        if args.log and log_file is not None:
            log_file.write(test_case_name + "\n")

    os.chdir(orig_dir)
    print("")

    if args.log and log_file is not None:
        log_file.close()
