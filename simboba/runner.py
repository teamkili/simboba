"""Eval runner - loads config and executes evaluations."""

import importlib.util
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from simboba.eval import Eval


@dataclass
class CaseResult:
    """Result of running a single eval case."""
    case_id: int
    passed: bool
    actual_output: Optional[str] = None
    judgment: Optional[str] = None
    reasoning: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


@dataclass
class RunResult:
    """Result of an entire eval run."""
    passed: int
    failed: int
    total: int
    score: float
    results: list[CaseResult]
    error_message: Optional[str] = None


def load_config(config_path: str) -> dict[str, Eval]:
    """Load eval configurations from a Python file.

    Returns a dict mapping eval names to Eval instances.
    """
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load the module
    spec = importlib.util.spec_from_file_location("eval_config", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load config file: {config_path}")

    module = importlib.util.module_from_spec(spec)

    # Add the config file's directory to sys.path so imports work
    config_dir = str(path.parent)
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Error loading config file: {e}")

    # Find all Eval instances in the module
    evals = {}
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, Eval):
            evals[obj.name] = obj

    if not evals:
        raise ValueError(f"No Eval instances found in {config_path}")

    return evals


@dataclass
class LoadResult:
    """Result of loading eval files."""
    evals: dict[str, "Eval"]
    loaded: list[tuple[str, list[str]]]  # [(filename, [eval_names]), ...]
    failed: list[tuple[str, str]]  # [(filename, error_message), ...]


def load_evals_folder(folder_path: str = "evals", return_details: bool = False) -> dict[str, Eval] | LoadResult:
    """Load all eval configurations from a folder.

    Scans the folder for .py files and loads all Eval instances from them.

    Args:
        folder_path: Path to the evals folder
        return_details: If True, returns LoadResult with success/failure details

    Returns:
        Dict of eval name -> Eval instance, or LoadResult if return_details=True
    """
    path = Path(folder_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Evals folder not found: {folder_path}")

    if not path.is_dir():
        raise ValueError(f"Not a directory: {folder_path}")

    all_evals = {}
    loaded = []
    failed = []
    py_files = list(path.glob("*.py"))

    if not py_files:
        raise ValueError(f"No Python files found in {folder_path}")

    for py_file in py_files:
        if py_file.name.startswith("_"):
            continue  # Skip __init__.py, __pycache__, etc.
        try:
            file_evals = load_config(str(py_file))
            all_evals.update(file_evals)
            loaded.append((py_file.name, list(file_evals.keys())))
        except Exception as e:
            failed.append((py_file.name, str(e)))

    if return_details:
        return LoadResult(evals=all_evals, loaded=loaded, failed=failed)

    if not all_evals:
        raise ValueError(f"No Eval instances found in {folder_path}")

    return all_evals


def run_case(eval_config: Eval, case: dict, judge_fn=None) -> CaseResult:
    """Run a single eval case and optionally judge the result.

    Args:
        eval_config: The Eval configuration
        case: Dict with 'id', 'inputs', 'expected_outcome'
        judge_fn: Optional function(inputs, expected, actual) -> (passed, reasoning)

    Returns:
        CaseResult with execution results
    """
    case_id = case["id"]
    inputs = case["inputs"]
    expected_outcome = case["expected_outcome"]

    start_time = time.time()

    try:
        # Run the eval function
        actual_output = eval_config.run(inputs)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # If we have a judge, use it
        if judge_fn:
            passed, reasoning = judge_fn(inputs, expected_outcome, actual_output)
            judgment = "PASS" if passed else "FAIL"
        else:
            # No judge - just record the output
            passed = False
            judgment = None
            reasoning = None

        return CaseResult(
            case_id=case_id,
            passed=passed,
            actual_output=str(actual_output),
            judgment=judgment,
            reasoning=reasoning,
            execution_time_ms=execution_time_ms,
        )
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return CaseResult(
            case_id=case_id,
            passed=False,
            error_message=str(e),
            execution_time_ms=execution_time_ms,
        )


def run_eval(eval_config: Eval, cases: list[dict], judge_fn=None) -> RunResult:
    """Run an eval against a list of cases.

    Args:
        eval_config: The Eval configuration
        cases: List of case dicts with 'id', 'inputs', 'expected_outcome'
        judge_fn: Optional function(inputs, expected, actual) -> (passed, reasoning)

    Returns:
        RunResult with all case results
    """
    results = []
    passed = 0
    failed = 0

    for case in cases:
        result = run_case(eval_config, case, judge_fn)
        results.append(result)

        if result.error_message:
            failed += 1
        elif result.passed:
            passed += 1
        else:
            failed += 1

    total = len(cases)
    score = (passed / total * 100) if total > 0 else 0.0

    return RunResult(
        passed=passed,
        failed=failed,
        total=total,
        score=score,
        results=results,
    )
