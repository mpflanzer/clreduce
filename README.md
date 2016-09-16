# 1. Info
This is basically a wrapper project which contains links (submodules) to all
tools required to reduce OpenCL kernels. Additionally it will contain the
interestingness tests which can be used during the reduction. Finally this
project will always point to version of the other tools that can be used
together.

Detailed information about the specific tools is provided by the original
authors.

* CLSmith: https://github.com/ChrisLidbury/CLSmith
* C-Reduce: https://github.com/csmith-project/creduce
* Oclgrind: https://github.com/jprice/Oclgrind
* LLVM: http://llvm.org
* Clang: http://clang.llvm.org
* libclc: http://libclc.llvm.org

# 2. Setup
## 2.1. Prerequisites

* Git
* Visual Studio *(Windows only)*
* m4 (_CLSmith_ header file generation)

### 2.1.1 Download all submodules
```
git submodule sync
git submodule init
git submodule update
```

### 2.1.2 C-Reduce dependencies
For a complete list please have a look at the C-Reduce repository.

* Flex
* Perl
    * Exporter::Lite
    * File::Which
    * Getopt::Tabular
    * Regexp::Common
    * _Sys::CPU (optional)_
    * _Term::ReadKey (optional)_

### 2.1.3 Interestingness test dependencies
The interestingness tests have been tested with the following version of Pyhton

* Pyhton 3.4 *(branch python34; deprecated)*
* Python 3.5

## 2.2. Configure and build CLSmith (optional) and cl_launcher
```
mkdir build_clsmith
cd build_clsmith
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../install ../CLSmith
cd ..
```

#### Windows
```
cmake --build ./build_clsmith --target INSTALL --config Release -- /m:8
```

#### Linux
```
cmake --build ./build_clsmith --target install --config Release -- -j 8
```

For instructions how to use _CLSmith_ and _cl_launcher_ please visit: http://multicore.doc.ic.ac.uk/tools/CLsmith/clsmith.php

## 2.3. Configure (and build) LLVM and Clang
```
mkdir build_llvm
cd build_llvm
cmake -DLLVM_EXTERNAL_CLANG_SOURCE_DIR=../clang -DLLVM_TARGETS_TO_BUILD=X86 -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../install ../llvm
cd ..
```

### 2.3.1 Build LLVM and Clang (optional, recommended)
If you already have a version of _LLVM_ and _Clang_ you can use it instead and do not have to rebuild it.

#### Windows
```
cmake --build ./build_llvm --target INSTALL --config Release -- /m:8
```

#### Linux
```
cmake --build ./build_llvm --target install --config Release -- -j 8
```
   
## 2.4. Configure and build Oclgrind
```
mkdir build_oclgrind
cd build_oclgrind
```

If you have build _LLVM_ and _Clang_ from the sources contained in this project (or _LLVM_ and _Clang_ are contained in your `PATH` environment) the command to generate the CMakeFiles for _Oclgrind_ does not need any customisation.

```
cmake -DCMAKE_INSTALL_PREFIX=../install -DCMAKE_BUILD_TYPE=Release ../Oclgrind
cd ..
```

Otherwise, if you previously skipped step 2.2.1 and your custom _LLVM_ and _Clang_ are not contained in your `PATH` environment you have to tell _Oclgrind_ explicitly where to find them.

```
cmake -DCMAKE_INSTALL_PREFIX=../install -DCMAKE_BUILD_TYPE=Release -DLLVM_DIR=path/to/llvm/share/llvm/cmake ../Oclgrind
cd ..
```

In either case the command to build _Oclgrind_ is the same.

#### Windows
```
cmake --build ./build_oclgrind --target INSTALL --config Release -- /m:8
```

**On Windows the build command might report errors for the targets "image", "vecadd" and "map_buffer". This is a problem with build Oclgrind internal tests which can be ignored.**

#### Linux
```
cmake --build ./build_oclgrind --target install --config Release -- -j 8
```

### 2.4.1 Register Oclgrind as platform (Windows only)
On Windows _Oclgrind_ has to be registered as custom OpenCL platform/device which can then be used as target in the host application. The steps are described in the orignal project page of _Oclgrind_.

> If you wish to use _Oclgrind_ via the OpenCL ICD (recommended), then you should also create an ICD loading point. To do this, you should add a `REG_DWORD` value to the Windows Registry under one or both of the registry keys below, with the name set to the absolute path of the `oclgrind-rt-icd.dll` library and the value set to `0`.
> 
> Key for **32-bit machines or 64-bit apps on a 64-bit machine**: `HKEY_LOCAL_MACHINE\SOFTWARE\Khronos\OpenCL\Vendors`
> 
> Key for **32-bit apps on a 64-bit machine**: `HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Khronos\OpenCL\Vendors`

## 2.5. Configure and build C-Reduce
```
mkdir build_creduce
cd build_creduce
cmake -DCMAKE_INSTALL_PREFIX=../install -DCMAKE_BUILD_TYPE=Release ../creduce
cd ..
```

#### Windows
```
cmake --build ./build_creduce --target INSTALL --config Release -- /m:8
```

#### Linux
```
cmake --build ./build_creduce --target install --config Release -- -j 8
```

## 2.6. Setup environment
All tools have been installed into `clreduce/install/bin`. To make the access to the tools easier it is recommended to add this directory to the `PATH` environment.

Header files are installed into `clreduce/install/include/`.

To run the provided _interestingness tests_ it is further required to set the environment variable `PYTHONPATH` to the path of the cloned `clreduce` directory.

Additionally, there are a few environment variables which are used to configure the interestingness tests and some other useful bits and pieces.

* **`CLSMITH_PATH`** (_not required for reductions themselves_):
    * Has to point to the `include/CLSmith` directory created by the _CLSmith_ project which contains required runtime header files
    * Used to automatically generate and pre-process test cases
* **`CREDUCE_LIBCLC_INCLUDE_PATH`**:
    * Has to point to the `generic/include` directory of the _libclc_ submodule
    * Required by C-Reduce to be able to parse OpenCL test cases
* **`CREDUCE_TEST_PLATFORM`**:
    * Has to be set to the number of the platform under test
* **`CREDUCE_TEST_DEVICE`**:
    * Has to be set to the number of the device under test
* **`CREDUCE_TEST_OCLGRIND_PLATFORM`** _(Windows only)_:
    * Has to be set to the number of the _Oclgrind_ platform
    * Required to run _Oclgrind_ from the interestingness tests as there is no wrapper script for Windows 
* **`CREDUCE_TEST_OCLGRIND_DEVICE`** _(Windows only)_:
    * Has to be set to the number of the _Oclgrind_ device
    * Required to run _Oclgrind_ from the interestingness tests as there is no wrapper script for Windows 
* **`CREDUCE_TEST_CL_LAUNCHER`** _(optional, default=`cl_launcher`)_:
    * Can be used to specify the _cl_launcher_ executable for the interestingness tests
    * If not specified the `PATH` environment is searched for `cl_launcher`
* **`CREDUCE_TEST_CLANG`** _(optional, default=`clang`)_:
    * Can be used to specify the _Clang_ executable for the interestingness tests
    * If not specified the `PATH` environment is searched for `clang`
* **`CREDUCE_TEST_TIMEOUT`** _(optional, default=`300`)_:
    * Timeout in seconds for each of the programs run during the interestingness test (not the overall runtime of the test)
* **`CREDUCE_TEST_USE_ORACLE`** _(optional, default=`1`)_:
    * Used by the _wrong-code-bug_ interestingness tests
    * If set to `1` _Oclgrind_ is used as oracle against which the output of _cl_launcher_ is compared to determine the interestingness of a test case
    * If set to `0` differential testing between the optimised and the unoptimised result is applied in the interestingness test
* **`CREDUCE_TEST_OPTIMISATION_LEVEL`** _(optional, default=`either`)_:
    * Only meaningful if `CREDUCE_TEST_USE_ORACLE` is set to `1`
    * Specifies the optimisation levels for which the outputs have to be different from the oracle to make a test case interesting
    * Possible values are `optimised`, `unoptimised`, `either` and `all`
* **`CREDUCE_TEST_CONSERVATIVE`** _(optional, default=`1`)_:
    * Controls whether the interstingness test checks that the result access in the kernel is only done by get_linear_global_id() and the this function is not changed
    * The additional checks are enabled if set to `1`
* **`CREDUCE_TEST_STATIC`** _(optional, default=`1`)_:
    * Controls whether the interstingness test includes static checks
    * Can be used to speed up testing of generated test cases if it can assumed they are valid
    * The static checks disabled if set to `0`

# 3. Running a reduction
The repository provides a helper script to simplify the steps from creating a test case with _CLSmith_ up to the actual reduction. This can involve the following (independent) steps:

* Generating test cases
* Preprocessing test cases to make them self-contained
* Checking which test cases are interesting
* Reducing work sizes (local, global) to speed up the reduction
* Reducing test cases

Not all arguments are going to be described in the following overview. The script has a built-in `--help` command to list all available arguments.

## 3.1 Generating test cases
The following command generates 1000 test cases using the _CLSmith_ mode `vectors` and stores them into the directory `vec1000_raw`.

```
python3 ./scripts/reduction_helper.py --generate 1000 --output vec1000_raw --modes vectors
```

If `--output` is not specified a new directory with a random name is created.

## 3.2 Preprocessing test cases
The following command takes the previously generated test cases, preprocesses them and stores them into a new directory.

```
python3 ./scripts/reduction_helper.py --test-case-dir ./vec1000_raw --preprocess --output vec1000_pre
```

Instead of a directory containing test cases it is also possible to specify an arbitrary number of test cases by using `--test-cases CLProg_X.cl CLProg_Y.cl [...]`.

## 3.3 Reducing the work sizes
The following command specifies that the input test cases are already preprocessed -- this means _CLSmith_ and its header files are not required --, and tries to reduce the global and local work sizes. This helps to speed up the reduction if the bug is still present when the test case is executed with a smaller work size.

```
python3 ./scripts/reduction_helper.py --test-case-dir ./vec1000_pre --preprocessed --output vec1000_rws --reduce-work-sizes-unchecked
```

The two possible options are `--reduce-work-sizes-checked` and `--reduce-work-sizes-unchecked`. The first one performs an interstingness test after each modification the latter one simply set the smallest possible value -- currently just one work item and one work group.

## 3.4 Testing for interestingness
The following command checks for each of the test cases if it is interesting according to the criterion specified as `--test` argument.

```
python3 ./scripts/reduction_helper.py --test-case-dir ./vec1000_rws --preprocessed --output vec1000_chk --test wrong-code-bug --check
```

The output directory contains only the test cases which have been determined to be interesting.

## 3.5 Reducing test cases
The following command reduces the specified test cases with respect to the criterion specified as `--test` argument.

```
python3 ./scripts/reduction_helper.py --test-case-dir ./vec1000_chk --preprocessed --output vec1000_red --test wrong-code-bug --reduce -n 4 --verbose
```

The argument `-n 4` specifies that _C-Reduce_ should use 4 interestingness test in parallel to speed up the reduction. _Because_ Oclgrind _is using a lot of memory for its undefined value check running many interestingness tests in parallel is likely  to cause out-of-memory situations._

The argument `--verbose` is passed to _C-Reduce_ and enables a more detailed logging of the reduction process.

## 3.6 Putting it all together
Instead of running all the commands one by one they can all be used in just one invocation.

```
python3 ./scripts/reduction_helper.py --generate 1000 --modes vectors barriers --preprocess --reduce-work-sizes-unchecked --output reduced --test wrong-code-bug --check --reduce -n 4 --verbose
```

# 4. Standalone interestingness tests
The interestingness tests are desgined in such a way that it is possible to call them from a command line. In this case the test case has to be passed as argument to the interestingness test.

```
python3 ./interestingness_tests/wrong_code_bug.py CLProg_0.cl
```

The script exits with status code `0` if the test case is considered interesting and `1` otherwise.
