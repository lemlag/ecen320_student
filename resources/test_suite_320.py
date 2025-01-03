#!/usr/bin/python3

import argparse
import os
import git
import subprocess
import time

import repo_test
from repo_test_suite import repo_test_suite

# ToDo:
# - Lab check script:
#   - The summaries at the end do not have enough informatino. Provide an option that givs more feedbak on what whet wrong and what to do (the log is so long i is hard to scroll back to see what happened)
#   - Fix up the error reporting (return error object instead of printing)
#   - Provide a link to the web page for instructions on how to address this problem
#   - Check to see if the student has changed the starter code locally
#   - Provide a way for having the simulation environment return an error when the testbench fails (lab 2)
#   - For uncommitted files, should we only check for the current directory or the entire repo?
# - tag flag
#   - The tag flag is used to checkout a specific tag before running the script. This is used to check out the code at the time of submission and run
#     It is different from the submit flag in that it does not actually tag the repository. Used for grading and checking code without resubmitting.
#   - Have the script return the checkout to main when done (or cache the current branch and return to current branch)
# - Submit Flag
#   - Other:
#     - Add ability to checkout entire repository to a temporary directory and run the script on that directory rather than the local directory

# Script changes:
# * flag to do a remote check like the TAs would do (default is local)
# * A step that sees if the starter code was updated as of the day the lab started
# * Flag to copy intermediate files during build before the clean occurs
# * Instructions on the passoff script

class test_suite_320(repo_test_suite):
    ''' 
    Represents a suite of tests to perform on a ECEN 320 repository. The tests are divided into several
    categories that are executed in a specific order:
        self.pre_build_tests: Tests that are run on the repository to check for integrity (before build)
        self.build_tests: Tests that are run involving a build process (generates temporary files, etc.)
        self.post_build_tests: Tests that are run after the build and before the clean (used for checking)
        self.clean_tests: Tests used to clean up and check the repository
    '''

    def __init__(self, repo, assignment_name, max_repo_files = 20, summary_log_filename = None,
                 required_executables = None, submit = False, starter_branch = "main"):
        super().__init__(repo, test_name = assignment_name, summary_log_filename = summary_log_filename)
        # Initialize the sets of tests
        self.repo_tests = []
        self.pre_build_tests = []
        self.build_tests = []
        self.post_build_tests = []
        self.clean_tests = []
        #self.add_pre_build_tests(max_repo_files, tag_str = assignment_name)
        self.add_repo_tests(max_repo_files, remote_branch = starter_branch)
        self.add_pre_build_tests()
        self.add_clean_tests()

        self.run_pre_build_tests = True
        self.run_build_tests = True
        self.run_post_build_tests = True
        self.run_clean_tests = True
        self.copy_file_dir = None # Location to copy generated build files
        self.prepend_file_str = None # String to prepend to the file name when copying
        self.required_executables = required_executables
        self.perform_submit = submit
        self.force = False

    def add_repo_tests(self, max_repo_files, tag_str = None, check_start_code = True, 
                            required_executables = None, remote_branch = "main"):
        """ Add tests that check the state of the repo """
        self.add_repo_test(repo_test.check_for_uncommitted_files())
        self.add_repo_test(repo_test.check_remote_origin())
        self.add_repo_test(repo_test.check_for_max_repo_files(max_repo_files))
        if check_start_code:
            self.add_repo_test(repo_test.check_remote_starter("startercode", remote_branch = remote_branch))
        if tag_str is not None:
            self.add_repo_test(repo_test.check_for_tag(tag_str))
        if required_executables is not None:
            self.add_repo_test(repo_test.execs_exist_test(required_executables))

    def add_pre_build_tests(self, required_executables = None):
        """ Add default tests that should be executed before any building. """
        if required_executables is not None:
            self.add_pre_build_test(repo_test.execs_exist_test(required_executables))

    def add_clean_tests(self):
        """ Add three repo clean tests (untracked files, make clean, and ignored files) """
        self.add_clean_test(repo_test.check_for_untracked_files())
        self.add_clean_test(repo_test.make_test("clean"))
        self.add_clean_test(repo_test.check_for_ignored_files())

    def add_repo_test(self,test):
        self.repo_tests.append(test)

    def add_pre_build_test(self,test):
        self.pre_build_tests.append(test)

    def add_build_test(self,test):
        self.build_tests.append(test)

    def add_post_build_test(self,test):
        self.post_build_tests.append(test)

    def add_clean_test(self,test):
        self.clean_tests.append(test)

    def add_Makefile_rule(self, make_rule, required_input_files = [], required_build_files = [], timeout_seconds = 10 * 60):
        ''' Add a makefile rule test '''
        make_test = repo_test.make_test(make_rule, required_input_files = required_input_files, 
                                        required_build_files = required_build_files,
                                        timeout_seconds=timeout_seconds)
        self.add_build_test(make_test)

    def add_required_files(self, file_list, check_files_not_tracked = False, check_tracked_files = False):
        ''' Add tests to see if a file exists.
        Optionally check to make sure it is not committed in the repo (for build files)
        optionally check to make sure it is committed in the repo (for required files) '''
        # Add test to see if the file was generated (in the current working directory)
        check_file_test = repo_test.file_exists_test(file_list, copy_dir = self.copy_file_dir, prepend_file_str = self.prepend_file_str)
        self.add_post_build_test(check_file_test)
        # Add test to make sure the file is not committed in the repository
        if check_files_not_tracked:
            non_committed_files_test = repo_test.file_not_tracked_test(file_list)
            self.add_post_build_test(non_committed_files_test)
        if check_tracked_files:
            committed_files_test = repo_test.files_tracked_test(file_list)
            self.add_post_build_test(committed_files_test)

    def add_required_tracked_files(self, file_list):
        self.add_required_files(file_list, check_tracked_files = True)

    def run_tests(self):
        """ Run all the registered tests in the test suite.
        """
        self.print_test_start_message()
        test_num = 1
        final_result = True
        # First run the repository tests
        if self.repo_tests:
            result = self.iterate_through_tests(self.repo_tests, start_step = test_num)
            test_num += len(self.repo_tests)
            final_result = final_result and result 
        if self.run_pre_build_tests:
            result = self.iterate_through_tests(self.pre_build_tests, start_step = test_num)
            test_num += len(self.pre_build_tests) 
            final_result = final_result and result 
        if self.run_build_tests:
            result = self.iterate_through_tests(self.build_tests, start_step = test_num)
            test_num += len(self.build_tests) 
            final_result = final_result and result 
        if self.run_post_build_tests:
            result = self.iterate_through_tests(self.post_build_tests, start_step = test_num)
            test_num += len(self.post_build_tests) 
            final_result = final_result and result 
        if self.run_clean_tests:
            result = self.iterate_through_tests(self.clean_tests, start_step = test_num)
            test_num += len(self.clean_tests) 
            final_result = final_result and result 
        if self.perform_submit and self.repo_tests:
            if not final_result:
                self.print_error("Cannot submit the lab due to errors in passoff script")
                return
            submit_status = self.submit_lab(self.test_name)
            if not submit_status:
                return
            check_commit_date_status = self.check_commit_date(self.test_name)
            if not check_commit_date_status:
                return
        self.print_test_end_message()

    def submit_lab(self, lab_name):
        ''' Passoff a lab assignment '''
        self.print(f"Attempting Submission for {lab_name}")
        result = repo_test.get_remote_tags()
        if not result:
            return False
        # Get all remote tags (is there a reliable way of doing this with Git Python?)
        # try:
        #     result = subprocess.run(["git fetch --tags"], shell=True, capture_output=True, text=True)
        #     print(result.stdout)
        # except subprocess.CalledProcessError as e:
        #     self.print_error(f"Error fetching tags: {e}")
        #     return False
        # Check if the tag exists in the repository
        tag = next((tag for tag in self.repo.tags if tag.name == lab_name), None)
        if tag is not None:
            #wirthlin@BYU-GCXHGWLQP6 lab01 % git push --delete origin lab01
            #wirthlin@BYU-GCXHGWLQP6 lab01 % git tag --delete lab01
            # Tag exists
        #     - If there is a tag:
        #       - Check to see if the tag code is different from the current commit. If not, exit saying it is already tagged and ready to submit
        #       - If the code is different, ask for permission to retag and push the tag to the remote. (ask for permission first unless '--force' flag is given)
            tag_commit = tag.commit
            current_commit = self.repo.head.commit
            commit_file_contents = repo_test.get_commit_file_contents(tag_commit, ".commitdate")
            if current_commit.hexsha == tag_commit.hexsha:
                print(f"Tag '{lab_name}' exists and is already up-to-date with the current commit.")
                if commit_file_contents is not None:
                    print(commit_file_contents)
            else:
                print(f"Tag '{lab_name}' exists and is out-of-date with the current commit.")
                if commit_file_contents is not None:
                    print(commit_file_contents)
                if self.force:
                    print("Forcing tag update")
                else:
                    print("Do you want to update the tag? Updating the tag will change the submission date.")
                    response = input("Enter 'yes' to update the tag: ")
                    if response.lower()[0] != 'y':
                        print("Tag update cancelled")
                        return False
                # Tag is out of date
                self.repo.delete_tag(lab_name)
                new_tag = self.repo.create_tag(lab_name)
                remote = self.repo.remote("origin")
                remote.push(new_tag, force=True)
        else:
            # Tag doesn't exist
            print(f"Tag '{lab_name}' does not exist in the repository. New tag will be created.")
            new_tag = self.repo.create_tag(lab_name)
            remote = self.repo.remote("origin")
            remote.push(new_tag)
        return True

    def check_commit_date(self, lab_name, timeout = 2 * 60, check_sleep_time = 10):
        ''' Iteratively check the commit date associated with a tag lab submission. 
        This is called after committing the lab to the repository to see if the commit date is updated.'''
        initial_time = time.time()
        first_time = True
        while True:
            # Wait for a bit before checking again if it isn't the first iteration
            if not first_time:
                print(f"Waiting to check for commit file")
                time.sleep(check_sleep_time)
                first_time = False

            # Fetch the remote tags
            result = repo_test.get_remote_tags()
            if not result:
                return False
            # See if the tag exists
            tag = next((tag for tag in self.repo.tags if tag.name == lab_name), None)
            if tag is None:
                time.sleep(check_sleep_time)
                continue
            # Tag exists, fetch the remote to get all the files
            repo_test.fetch_remote(self.repo)
            # Get the commit associated with the tag
            tag_commit = tag.commit
            # See if the .commitdate file exists in root of repository
            # Access the file from the commit
            file_path = ".commitdate"
            file_content = repo_test.get_commit_file_contents(tag_commit, file_path)
            if file_content is not None:
                self.print(f"Commit file created - submission complete")
                self.print(file_content)
                return True

            # Check if the timeout has been reached
            if time.time() - initial_time > timeout:
                print(f"Timeout reached for checking tag '{lab_name}' commit date.")
                return False
            self.print_error(f"Github Submission commit file '{file_path}' not yet created - waiting")
        return False

def build_test_suite_320(assignment_name, max_repo_files = 20, start_date = None):
    """ A helper function used by 'main' functions to build a test suite based on command line arguments.
    """
    parser = argparse.ArgumentParser(description=f"Test suite for 320 Assignment: {assignment_name}")
    parser.add_argument("--submit",  action="store_true", help="Submit the assignment to the remote repository (tag and push)")
    parser.add_argument("--repo", help="Path to the local repository to test (default is current directory)")
    parser.add_argument("--force", action="store_true", help="Force submit (no prompt)")
    parser.add_argument("--norepo", action="store_true", help="Do not run Repo tests")
    parser.add_argument("--nobuild", action="store_true", help="Do not run build tests")
    parser.add_argument("--noclean", action="store_true", help="Do not run clean tests")
    parser.add_argument("--log", type=str, help="Save output to a log file (relative file path)")
    parser.add_argument("--starterbranch", type=str, default = "main", help="Branch for starter code to check")
    parser.add_argument("--copy", type=str, help="Copy generated files to a directory")
    parser.add_argument("--copy_file_str", type=str, help="Customized the copy file by prepending filenames with given string")
    args=parser.parse_args()

    # Get repo
    if args.repo is None:
        path = os.getcwd()
    else:
        path = args.repo
    repo = git.Repo(path, search_parent_directories=True)

    # Log file
    summary_log_filename = None
    if args.log is not None:
        summary_log_filename = args.log

    # Build test suite
    test_suite = test_suite_320(repo, assignment_name,
        max_repo_files = max_repo_files, summary_log_filename = summary_log_filename, submit = args.submit,
        starter_branch = args.starterbranch)
    test_suite.force = args.force

    # Decide which tests to run
    if args.norepo:
        test_suite.run_pre_build_tests = False
    if args.nobuild:
        test_suite.run_build_tests = False
    if args.noclean:
        test_suite.run_clean_tests = False
    # See if a copy of the build files are needed and if so, customize the copy
    if args.copy:
        test_suite.copy_file_dir = args.copy
        print(f"Copying files to {args.copy}")
        if args.copy_file_str:
            test_suite.prepend_file_str = args.copy_file_str
    return test_suite

class get_err_git_commits(repo_test.repo_test):
    ''' Prints the commits of the given directory in the repo.
    '''
    def __init__(self, min_msgs, check_path = None, check_str = "ERR"):
        '''  '''
        super().__init__()
        self.check_path = check_path
        self.min_msgs = min_msgs
        self.check_str = check_str

    def module_name(self):
        return "Check for minimum number of error commits"

    def perform_test(self, repo_test_suite):
        if self.check_path is None:
            self.check_path = repo_test_suite.working_path

        relative_path = self.check_path.relative_to(repo_test_suite.repo_root_path)
        repo_test_suite.print(f'Checking for ERR commits in {relative_path}')
        commits = list(repo_test_suite.repo.iter_commits(paths=relative_path))
        chk_commits = []
        for commit in commits:
            commit_message = commit.message.strip()
            if self.check_str in commit_message:
                chk_commits.append(commit_message)
                print(commit_message)
        if len(chk_commits) >= self.min_msgs:
            # return True
            return self.success_result()
        else:
            repo_test_suite.print_error(f"Insufficient number of error commits: found {len(chk_commits)} but expecting {self.min_msgs}")
            # return False
            return self.warning_result()
