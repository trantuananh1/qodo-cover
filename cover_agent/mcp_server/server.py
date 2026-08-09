from fastmcp import FastMCP
import asyncio
from pathlib import Path
import sys

mcp = FastMCP("vCover")

test = {"counter": 0}
jobs = {}

async def run_and_update_job(job_id, command_list, cwd):
    proc = await asyncio.create_subprocess_exec(
        *command_list,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd
    )
    jobs[job_id]['process'] = proc
    stdout, stderr = await proc.communicate()
    jobs[job_id]['status'] = 'completed' if proc.returncode == 0 else 'failed'
    jobs[job_id]['stdout'] = stdout.decode(errors='ignore')
    jobs[job_id]['stderr'] = stderr.decode(errors='ignore')
    jobs[job_id]['returncode'] = proc.returncode
    del jobs[job_id]['process']

# async def sleep_and_update_job(job_id, seconds):
#     try:
#         # Execute the tool function (e.g., delayed_message)
#         await asyncio.sleep(seconds)
#         result = f"[Run {job_id}] Slept for {seconds/3600} hours and now returning this message lol."
#         jobs[job_id]['status'] = 'completed'
#         jobs[job_id]['result'] = result
#     except Exception as e:
#         jobs[job_id]['status'] = 'failed'
#         jobs[job_id]['error'] = str(e)

# @mcp.tool()
# async def delayed_message(seconds: int = 5) -> dict:
#     """
#     Sleeps for a given number of seconds before returning a message.
#
#     Args:
#         seconds (int): How long to sleep (default 5 seconds)
#     Returns:
#         dict: A message with the job id of the processing of the delayed message
#     """
#     # test['counter'] += 1
#     # await asyncio.sleep(seconds)
#     #
#     # return f"[Run {test['counter']}] Slept for {seconds/3600} hours and now returning this message lol."
#     job_id = len(jobs) + 1
#     jobs[job_id] = {
#         "status": "running",
#         "tool": "delayed_message",
#         "params": {"seconds": seconds},
#         "result": None
#     }
#
#     # Start the delayed_message tool in the background
#     asyncio.create_task(sleep_and_update_job(job_id, seconds))
#
#     return {"job_id": job_id}

@mcp.tool()
async def improve_coverage_for_entire_repository(
    project_language: str,
    code_coverage_report_path: str,
    test_command: str,
    project_root: str = ".",
    cwd: str = ".",
    max_test_files_allowed_to_analyze: int = None,
    look_for_oldest_unchanged_test_file: bool = None,
    test_folder: str = None,
    test_file: str = None,
    run_each_test_seperately: bool = None,
    test_command_dir: str = None,
    coverage_type: str = None,
    report_filepath: str = None,
    max_iterations: int = None,
    max_run_time_sec: int = None,
    additional_instructions: str = None,
    model: str = None,
    api_base: str = None,
    strict_coverage: bool = None,
    run_tests_multiple_times: int = None,
    log_db_path: str = None,
    test_file_output_path: str = None,
    desired_coverage: int = None,
    branch: str = None,
    record_mode: bool = None,
    suppress_log_files: bool = None,
    use_report_coverage_feature_flag: bool = None,
    diff_coverage: bool = None
):
    """
    Tool: improve_coverage_for_entire_repository
    Description:
        **Primary Function: Automated Test Generation and File Modification for an Entire Repository (Asynchronous).**
        This tool runs the cover-agent-full-repo command line program, which initiates an asynchronous process to scan an *entire repository*, identify testable source files,
        and their corresponding test files. It then automatically generates new unit tests to increase overall
        code coverage across the project. The generated tests are **directly appended to the respective test files
        on the file system.**

        **Asynchronous Operation:** This tool immediately returns a `job_id`. The actual test generation and file
        modification happen in the background. To check the status or retrieve the final results (stdout, stderr,
        returncode) of the operation, you must use the `get_job_details` tool with the returned `job_id`.

        **When to Use This Tool:**
        Use this tool when your goal is to improve the overall test coverage of an entire codebase, rather than
        focusing on a single file. This is suitable for initial coverage efforts or for maintaining a high level
        of test coverage across a project.

        **Transient Failures (LSP Startup):** The underlying `cover-agent` process may occasionally fail on startup, particularly if it involves Language Server Protocol (LSP) initialization. If a job fails with an error that suggests a startup issue, it is often a transient problem. In such cases, **the recommended action is to retry the tool call.**

        **Do NOT attempt to run the `test_command` or generate coverage reports yourself before calling this tool.**
        The tool will execute the provided `test_command` internally to generate the coverage report and validate tests.
        Provide the necessary project details and commands, and this tool will handle the entire test generation,
        validation, and file modification process across multiple files.

    Workflow:
    1. You provide the absolute path to the project's root directory (e.g., `/path/to/my_project`) as `cwd`.
    2. You specify the primary programming language of the project (e.g., "python", "java").
    3. You provide the command to run the existing tests and generate a coverage report (e.g., "mvn verify -DfailIfNoTest=false").
       **The tool will execute this `test_command` internally as part of its operation.**
    4. The tool returns a `job_id`.
    5. You use the `get_job_details` tool with the `job_id` to monitor the job's progress and retrieve its final output.

    Parameters:
    -----------
    --- Required ---

        project_language (string):
        The primary programming language of the project (e.g., "python", "java", "typescript").
        This is crucial for the tool to correctly identify and analyze files.

        code_coverage_report_path (string):
        The absolute path to the code coverage report file (e.g., `/path/to/my_project/coverage.xml`).
        The tool uses this report to identify untested code lines across the repository.

        test_command (string):
        The shell command required to run the entire test suite and generate the coverage report.
        **This command will be executed by the tool internally.**
        Example: `"mvn verify -DfailIfNoTest=false"`

    --- Optional ---

        cwd (string):
        **CRITICAL:** The absolute path to the project's root directory. This is the directory
        where the `cover-agent` tool will be executed. For example, if your project is at
        `/home/user/my_python_app`, then `cwd` should be `/home/user/my_python_app`.
        This parameter is essential for the tool to correctly locate files and execute commands
        within the project context.

        project_root (string):
        **IMPORTANT:** This parameter should almost always be set to `"."` (a single dot).
        It specifies the root of the repository *relative to the `cwd`*. Setting it to anything
        other than `"."` can lead to internal bugs within the `cover-agent` processing.
        Ensure `cwd` is the absolute path to your project, and `project_root` remains `"."`.
        Defaults to `"."`.

        max_test_files_allowed_to_analyze (integer):
        The maximum number of test files the tool will analyze and attempt to improve coverage for.
        This can be used to limit the scope of a run.

        look_for_oldest_unchanged_test_file (boolean):
        If true, the tool will prioritize analyzing the oldest test files that have not been
        modified recently, focusing on areas that might have been neglected.

        test_folder (string):
        A relative path (from `project_root`) to a specific folder containing tests to analyze.
        If provided, the tool will only consider test files within this folder.

        test_file (string):
        A relative path (from `project_root`) to a specific test file to extend.
        If provided, the tool will focus on improving this single test file within the repository.

        run_each_test_seperately (boolean):
        If true, each generated test will be run in a separate process during validation.

        test_command_dir (string):
        The absolute path to the directory where the test command should be executed.
        Defaults to the project root.

        coverage_type (string):
        The type of coverage report being used (e.g., "jacoco", "lcov", "cobertura").
        Defaults to the value in the configuration file.

        report_filepath (string):
        The absolute path to the output report file generated by the tool.

        desired_coverage (integer):
        The target overall coverage percentage (0-100) for the repository. The tool will stop
        generating tests once this coverage level is achieved or exceeded. Defaults to the
        value in the configuration file.

        max_iterations (integer):
        The maximum number of attempts the tool will make to generate new tests across the repository.
        Defaults to the value in the configuration file.

        max_run_time_sec (integer):
        The maximum time in seconds allowed for the test command to run during each validation step.

        additional_instructions (string):
        Any specific instructions or context you wish to provide to the LLM when it generates tests.
        Example: "Ensure new tests integrate well with existing Maven Surefire configurations."

        model (string):
        The name of the LLM model to use for generating tests. Defaults to the
        value in the configuration file.

        api_base (string):
        The base URL for the LLM API (e.g., for Ollama or Hugging Face).

        strict_coverage (boolean):
        If true, the tool will exit with a non-zero status code if the desired
        coverage is not achieved.

        run_tests_multiple_times (integer):
        The number of times to run each newly generated test to ensure its stability and reliability.
        Defaults to the value in the configuration file.

        log_db_path (string):
        The absolute path to an optional SQLite database file for logging detailed test generation
        and validation results.

        branch (string):
        The Git branch to compare against when using `diff_coverage`.

        record_mode (boolean):
        If true, the LLM responses will be recorded for replay or analysis.

        suppress_log_files (boolean):
        If true, all generated log files (HTML, logs, DB files) will be suppressed.

    --- Mutually Exclusive Options ---

        use_report_coverage_feature_flag (boolean):
        If true, the tool will consider the coverage of all files in the
        coverage report when determining if a new test is useful. This means a test is
        considered good if it increases coverage for any file, not just the source file.
        Incompatible with `diff_coverage`.

        diff_coverage (boolean):
        If true, the tool will only generate tests for code changes (diff) between the
        current branch and the branch specified by `branch`. This is useful for
        focusing on new or modified code. Incompatible with `use_report_coverage_feature_flag`.

    Returns:
    --------
        dict:
            A dictionary containing the `job_id` (string) for the asynchronous operation.
            You must use the `get_job_details` tool with this `job_id` to retrieve the
            final status, stdout, stderr, and returncode of the test generation process.

    Example Usage:
    --------------
    To improve overall Python project coverage for a repository at `/home/user/my_python_app`,
    aiming for 85% coverage:
    default_api.improve_coverage_for_entire_repository(
        project_language="python",
        code_coverage_report_path="/home/user/my_python_app/coverage.xml",
        test_command="pytest --cov=/home/user/my_python_app --cov-report=xml:/home/user/my_python_app/coverage.xml",
        cwd="/home/user/my_python_app",
        project_root=".",
        desired_coverage=85,
        max_iterations=5
    )
    """
    if use_report_coverage_feature_flag and diff_coverage:
       raise ValueError("Cannot use both 'use_report_coverage_feature_flag' and 'diff_coverage' at the same time.")
    python_executable = sys.executable
    if not python_executable:
        raise RuntimeError("Could not determine the python executable path.")

    # --- Build the command as a list ---
    command_list = [
        python_executable,
        "-m",
        "cover_agent.main_full_repo",
        "--project-language", project_language,
        "--project-root", project_root,
        "--code-coverage-report-path", code_coverage_report_path,
        "--test-command", test_command,
    ]

    # --- Append optional arguments ---
    if max_test_files_allowed_to_analyze:
        command_list.extend(["--max-test-files-allowed-to-analyze", str(max_test_files_allowed_to_analyze)])
    if look_for_oldest_unchanged_test_file:
        command_list.append("--look-for-oldest-unchanged-test-file")
    if test_folder:
        command_list.extend(["--test-folder", test_folder])
    if test_file:
        command_list.extend(["--test-file", test_file])
    if run_each_test_seperately:
        command_list.append("--run-each-test-separately")
    if test_command_dir:
        command_list.extend(["--test-command-dir", test_command_dir])
    if coverage_type:
        command_list.extend(["--coverage-type", coverage_type])
    if report_filepath:
        command_list.extend(["--report-filepath", report_filepath])
    if max_iterations:
        command_list.extend(["--max-iterations", str(max_iterations)])
    if max_run_time_sec:
        command_list.extend(["--max-run-time-sec", str(max_run_time_sec)])
    if additional_instructions:
        command_list.extend(["--additional-instructions", additional_instructions])
    if model:
        command_list.extend(["--model", model])
    if api_base:
        command_list.extend(["--api-base", api_base])
    if strict_coverage:
        command_list.append("--strict-coverage")
    if run_tests_multiple_times:
        command_list.extend(["--run-tests-multiple-times", str(run_tests_multiple_times)])
    if log_db_path:
        command_list.extend(["--log-db-path", log_db_path])
    if test_file_output_path:
        command_list.extend(["--test-file-output-path", test_file_output_path])
    if desired_coverage:
        command_list.extend(["--desired-coverage", str(desired_coverage)])
    if branch:
        command_list.extend(["--branch", branch])
    if record_mode:
        command_list.append("--record-mode")
    if suppress_log_files:
        command_list.append("--suppress-log-files")
    if use_report_coverage_feature_flag:
        command_list.append("--use-report-coverage-feature-flag")
    if diff_coverage:
        command_list.append("--diff-coverage")

    job_id = len(jobs) + 1
    jobs[job_id] = {
        "status": "running",
        "command": command_list,
        "stdout": "",
        "stderr": "",
        "returncode": None
    }
    asyncio.create_task(run_and_update_job(job_id, command_list, cwd))

    return {"job_id": job_id}
    # stdout, stderr = await proc.communicate()
    # return job_id, proc.returncode, command_list


@mcp.tool()
async def get_job_details(job_id: int) -> dict:
    """
    Retrieves the details of a job.

    Args:
        job_id (int): The ID of the job to retrieve.
    Returns:
        dict: A dictionary containing the job's details.
    """
    job = jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}

    # Don't return the process object, it's not JSON serializable
    return {k: v for k, v in job.items() if k != 'process'} 

@mcp.tool()
async def improve_coverage_for_single_file(
    source_file_path: str,
    test_file_path: str,
    code_coverage_report_path: str,
    test_command: str,
    project_root: str = None,
    cwd: str = ".",
    test_command_dir: str = None,
    coverage_type: str = None,
    report_filepath: str = None,
    max_iterations: int = None,
    max_run_time_sec: int = None,
    additional_instructions: str = None,
    model: str = None,
    api_base: str = None,
    strict_coverage: bool = None,
    run_tests_multiple_times: int = None,
    log_db_path: str = None,
    test_file_output_path: str = None,
    desired_coverage: int = None,
    branch: str = None,
    record_mode: bool = None,
    suppress_log_files: bool = None,
    run_each_test_separately: bool = None,
    use_report_coverage_feature_flag: bool = None,
    diff_coverage: bool = None,
    included_files: list[str] = None
):
    """
    Tool: improve_coverage_for_single_file
    Description:
        **Primary Function: Automated Test Generation and File Modification for a Single File (Asynchronous).**
        This tool initiates an asynchronous process to automatically generate new unit tests for a
        *single specified source code file* to increase its code coverage. It analyzes the source code,
        identifies lines not covered by existing tests, and then intelligently writes new test cases.
        The generated tests are **directly appended to the specified test file on the file system.**

        **Asynchronous Operation:** This tool immediately returns a `job_id`. The actual test generation and file
        modification happen in the background. To check the status or retrieve the final results (stdout, stderr,
        returncode) of the operation, you must use the `get_job_details` tool with the returned `job_id`.

        **When to Use This Tool:**
        Use this tool when you have a specific source file (e.g., `my_module.py`) and its corresponding test file
        (e.g., `test_my_module.py`) and your goal is to improve the test coverage for that particular source file.

        **Transient Failures (LSP Startup):** The underlying `cover-agent` process may occasionally fail on startup, particularly if it involves Language Server Protocol (LSP) initialization. If a job fails with an error that suggests a startup issue, it is often a transient problem. In such cases, **the recommended action is to retry the tool call.**

        **Do NOT attempt to run the `test_command` or generate coverage reports yourself before calling this tool.**
        The tool will execute the provided `test_command` internally to generate the coverage report and validate tests.
        Provide the necessary file paths and arguments, and this tool will handle the entire test generation,
        validation, and file modification process.

    Workflow:
    1. You provide the absolute path to the source code file you want to test (e.g., `/path/to/project/src/my_module.py`).
    2. You provide the absolute path to the associated test file where new tests should be added (e.g., `/path/to/project/tests/test_my_module.py`).
    3. You provide the command to run the existing tests and generate a coverage report (e.g., `"pytest --cov=/app --cov-report=xml:/app/calculator.py --cov-report=xml:/app/coverage.xml"`).
       **The tool will execute this `test_command` internally as part of its operation.**
    4. The tool returns a `job_id`.
    5. You use the `get_job_details` tool with the `job_id` to monitor the job's progress and retrieve its final output.

    Parameters:
    -----------
    --- Required ---

        source_file_path (string):
        The absolute path to the single source file (e.g., `/path/to/project/src/my_module.py`)
        that you want to improve test coverage for.

        test_file_path (string):
        The absolute path to the existing test file (e.g., `/path/to/project/tests/test_my_module.py`)
        that this tool will **read from and directly append new tests to.**

        code_coverage_report_path (string):
        The absolute path to the code coverage report file (e.g., `/path/to/project/coverage.xml`).
        The tool uses this report to identify untested code lines.

        test_command (string):
        The shell command required to run the entire test suite and generate the coverage report.
        **This command will be executed by the tool internally.**
        Example: `"pytest --cov=/app --cov-report=xml:/app/calculator.py --cov-report=xml:/app/coverage.xml"`

    --- Optional ---

        cwd (string):
        **CRITICAL:** The absolute path to the project's root directory. This is the directory
        where the `cover-agent` tool will be executed. For example, if your project is at
        `/home/user/my_python_app`, then `cwd` should be `/home/user/my_python_app`.
        This parameter is essential for the tool to correctly locate files and execute commands
        within the project context.

        project_root (string):
        **IMPORTANT:** This parameter should almost always be set to `"."` (a single dot).
        It specifies the root of the project *relative to the `cwd`*. Setting it to anything
        other than `"."` can lead to internal bugs within the `cover-agent` processing.
        Ensure `cwd` is the absolute path to your project, and `project_root` remains `"."`.
        Defaults to None because cover-agent don't require `project_root` to run

        test_file_output_path (string):
        The absolute path to a new file where the modified test file should be written.
        If provided, the tool will **write the complete, modified test file to this new path**
        instead of overwriting the original file specified by `test_file_path`.

        test_command_dir (string):
        The absolute path to the directory where the test command should be executed.
        Defaults to the project root.

        included_files (list of strings):
        A list of absolute file paths to include in the coverage analysis. This is useful when
        the coverage report contains information about files that are not directly related to
        the source file, but whose coverage is relevant to the overall goal.
        Example: `["/path/to/project/src/helper.py", "/path/to/project/src/utils.py"]`

        coverage_type (string):
        The type of coverage report being used (e.g., "jacoco", "lcov", "cobertura").
        Defaults to the value in the configuration file.

        report_filepath (string):
        The absolute path to the output report file generated by the tool.

        desired_coverage (integer):
        The target coverage percentage (0-100). The tool will stop generating tests
        once this coverage level is achieved or exceeded. Defaults to the value in the
        configuration file.

        max_iterations (integer):
        The maximum number of attempts the tool will make to generate new tests.
        Defaults to the value in the configuration file.

        max_run_time_sec (integer):
        The maximum time in seconds allowed for the test command to run during each validation step.

        additional_instructions (string):
        Any specific instructions or context you wish to provide to the LLM when it generates tests.
        Example: "Focus on edge cases for negative numbers and zero."

        model (string):
        The name of the LLM model to use for generating tests. Defaults to the
        value in the configuration file.

        api_base (string):
        The base URL for the LLM API (e.g., for Ollama or Hugging Face).

        strict_coverage (boolean):
        If true, the tool will exit with a non-zero status code if the desired
        coverage is not achieved.

        run_tests_multiple_times (integer):
        The number of times to run each newly generated test to ensure its stability and reliability.
        Defaults to the value in the configuration file.

        log_db_path (string):
        The absolute path to an optional SQLite database file for logging detailed test generation
        and validation results.

        branch (string):
        The Git branch to compare against when using `diff_coverage`.

        run_each_test_separately (boolean):
        If true, each generated test will be run in a separate process during validation.

        record_mode (boolean):
        If true, the LLM responses will be recorded for replay or analysis.

        suppress_log_files (boolean):
        If true, all generated log files (HTML, logs, DB files) will be suppressed.

    --- Mutually Exclusive Options ---

        use_report_coverage_feature_flag (boolean):
        If true, the tool will consider the coverage of all files in the
        coverage report when determining if a new test is useful. This means a test is
        considered good if it increases coverage for any file, not just the source file.
        Incompatible with `diff_coverage`.

        diff_coverage (boolean):
        If true, the tool will only generate tests for code changes (diff) between the
        current branch and the branch specified by `branch`. This is useful for
        focusing on new or modified code. Incompatible with `use_report_coverage_feature_flag`.

    Returns:
    --------
        dict:
            A dictionary containing the `job_id` (string) for the asynchronous operation.
            You must use the `get_job_details` tool with this `job_id` to retrieve the
            final status, stdout, stderr, and returncode of the test generation process.

    Example Usage:
    --------------
    To improve coverage for `src/calculator.py` by adding tests to `tests/test_calculator.py`
    within a project located at `/app`, aiming for 90% coverage:
    default_api.improve_coverage_for_single_file(
        source_file_path="/app/src/calculator.py",
        test_file_path="/app/tests/test_calculator.py",
        code_coverage_report_path="/app/coverage.xml",
        test_command="pytest --cov=/app --cov-report=xml:/app/calculator.py --cov-report=xml:/app/coverage.xml",
        cwd="/app",
        desired_coverage=90,
        additional_instructions="Focus on edge cases for addition and subtraction, especially with zero and negative numbers."
    )
    """
    if use_report_coverage_feature_flag and diff_coverage:
        raise ValueError("Cannot use both 'use_report_coverage_feature_flag' and 'diff_coverage' at the same time.")

    python_executable = sys.executable
    if not python_executable:
        raise RuntimeError("Could not determine the python executable path.")

    command_list = [
        python_executable,
        "-m",
        "cover_agent.main",
        "--source-file-path", source_file_path,
        "--test-file-path", test_file_path,
        "--code-coverage-report-path", code_coverage_report_path,
        "--test-command", test_command,
    ]

    if project_root:
        command_list.extend(["--project-root", project_root])
    if test_file_output_path:
        command_list.extend(["--test-file-output-path", test_file_output_path])
    if test_command_dir:
        command_list.extend(["--test-command-dir", test_command_dir])
    if included_files:
        command_list.append("--included-files")
        command_list.extend(included_files)
    if coverage_type:
        command_list.extend(["--coverage-type", coverage_type])
    if report_filepath:
        command_list.extend(["--report-filepath", report_filepath])
    if desired_coverage:
        command_list.extend(["--desired-coverage", str(desired_coverage)])
    if max_iterations:
        command_list.extend(["--max-iterations", str(max_iterations)])
    if max_run_time_sec:
        command_list.extend(["--max-run-time-sec", str(max_run_time_sec)])
    if additional_instructions:
        command_list.extend(["--additional-instructions", additional_instructions])
    if model:
        command_list.extend(["--model", model])
    if api_base:
        command_list.extend(["--api-base", api_base])
    if strict_coverage:
        command_list.append("--strict-coverage")
    if run_tests_multiple_times:
        command_list.extend(["--run-tests-multiple-times", str(run_tests_multiple_times)])
    if log_db_path:
        command_list.extend(["--log-db-path", log_db_path])
    if branch:
        command_list.extend(["--branch", branch])
    if run_each_test_separately:
        command_list.append("--run-each-test-separately")
    if record_mode:
        command_list.append("--record-mode")
    if suppress_log_files:
        command_list.append("--suppress-log-files")
    if use_report_coverage_feature_flag:
        command_list.append("--use-report-coverage-feature-flag")
    if diff_coverage:
        command_list.append("--diff-coverage")

    job_id = len(jobs) + 1
    jobs[job_id] = {
        "status": "running",
        "command": command_list,
        "stdout": "",
        "stderr": "",
        "returncode": None
    }
    asyncio.create_task(run_and_update_job(job_id, command_list, cwd))
    
    return {"job_id": job_id}

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
