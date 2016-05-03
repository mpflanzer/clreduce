#!/usr/bin/env python3

import re

class WorkSizeReducer:
    def __init__(self, test_case, test):
        self.test_case = open(test_case, "r+")
        self.test = test
        test_case_content = self.test_case.read()

        work_sizes_match = re.search(r"//(.*) -g ([0-9]+),([0-9]+),([0-9]+) -l ([0-9]+),([0-9]+),([0-9]+)\n", test_case_content)

        if work_sizes_match is not None:
            self.meta_information = work_sizes_match.group(1)
            self.orig_global_work_size = (work_sizes_match.group(2), work_sizes_match.group(3), work_sizes_match.group(4))
            self.orig_local_work_size = (work_sizes_match.group(5), work_sizes_match.group(6), work_sizes_match.group(7))
            self.test_case_content = test_case_content.replace(work_sizes_match.group(0), "")

    def __del__(self):
        self.test_case.close()

    def __rewrite_work_sizes(self, global_work_size, local_work_size):
        self.test_case.seek(0)
        self.test_case.truncate()
        self.test_case.write("//{0} -g {1[0]},{1[1]},{1[2]} -l {2[0]},{2[1]},{2[2]}\n".format(self.meta_information, global_work_size, local_work_size))
        self.test_case.write(self.test_case_content)
        self.test_case.flush()

    def __update_work_sizes(global_work_size, local_work_size):
        #FIXME: Come up with a better algorithm
        local_work_size = [s + 1 for s in local_work_size]

        for i in range(0, len(global_work_size)):
            while global_work_size[i] % local_work_size[i] != 0:
                global_work_size[i] += 1

        return (global_work_size, local_work_size)

    def run(self, checked):
        new_global_work_size = [1] * len(self.orig_global_work_size)
        new_local_work_size = [1] * len(self.orig_local_work_size)

        if checked == False:
            self.__rewrite_work_sizes(new_global_work_size, new_local_work_size)
            return True

        while not self.test.check():
            (new_global_work_size, new_local_work_size) = self.__update_work_sizes(new_global_work_size, new_local_work_size)

            if (new_global_work_size == self.orig_global_work_size and
                new_local_work_size == self.orig_local_work_size):
                return False

        self.__rewrite_work_sizes(new_global_work_size, new_local_work_size)

        return True
