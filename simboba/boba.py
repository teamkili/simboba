"""
Boba - Simple eval tracking.

Usage:
    from simboba import Boba

    boba = Boba()

    # Single eval
    boba.eval(input="Hello", output="Hi there!", expected="Should greet the user")

    # Dataset eval
    boba.run(agent_fn, dataset="my-dataset")
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Optional, Union

from simboba import storage
from simboba.schemas import AgentResponse, MessageInput

# Type alias for metadata checker function
MetadataChecker = Callable[[Optional[dict], Optional[dict]], bool]

# Type alias for agent function - receives full inputs list, can return str or AgentResponse
AgentCallable = Callable[[list[MessageInput]], Union[str, AgentResponse]]


class Boba:
    """Simple eval tracking."""

    def __init__(self):
        """Initialize Boba."""
        self._warned_simple_judge = False

    def _get_judge(self, warn: bool = True, prompt: str = None):
        """Get the judge function.

        Args:
            warn: Whether to print a warning if falling back to simple judge
            prompt: Custom prompt template for the judge. If not specified, uses default.

        Returns:
            Judge function
        """
        try:
            from simboba.judge import create_judge
            model = storage.get_setting("model")
            return create_judge(model=model, prompt=prompt)
        except Exception:
            if warn and not self._warned_simple_judge:
                print("\n  No API key found. Using simple keyword-matching judge.")
                print("   For better results, set ANTHROPIC_API_KEY in your environment.")
                print("   See: https://console.anthropic.com/\n")
                self._warned_simple_judge = True
            from simboba.judge import create_simple_judge
            return create_simple_judge()

    # Fixed ID for ad-hoc evals (not part of a dataset)
    ADHOC_DATASET_ID = "_adhoc"

    def eval(
        self,
        input: str,
        output: str,
        expected: str,
        name: Optional[str] = None,
        expected_metadata: Optional[dict] = None,
        actual_metadata: Optional[dict] = None,
        metadata_checker: Optional[MetadataChecker] = None,
        judge_prompt: Optional[str] = None,
    ) -> dict:
        """
        Evaluate a single input/output pair.

        Args:
            input: The input message
            output: The actual output from your agent
            expected: What the output should do/contain
            name: Optional name for this eval
            expected_metadata: Expected metadata (citations, tool_calls, etc.)
            actual_metadata: Actual metadata from the agent response
            metadata_checker: Optional function(expected, actual) -> bool for
                            deterministic metadata checking. If not provided,
                            metadata is passed to the LLM judge.
            judge_prompt: Custom prompt template for the judge. If not provided,
                         uses default. Available placeholders: {conversation},
                         {expected_outcome}, {expected_metadata_section},
                         {actual_output}, {actual_metadata_section}

        Returns:
            dict with: passed, reasoning, run_id
        """
        # Create run record
        run = {
            "dataset_id": self.ADHOC_DATASET_ID,
            "dataset_name": "_adhoc",
            "eval_name": name or "single-eval",
            "status": "running",
            "total": 1,
            "passed": 0,
            "failed": 0,
            "started_at": datetime.now().isoformat(),
            "results": {},
        }

        # Judge the output (always pass metadata to LLM when provided)
        judge_fn = self._get_judge(prompt=judge_prompt)
        inputs = [{"role": "user", "message": input}]
        output_passed, reasoning = judge_fn(
            inputs, expected, output,
            expected_metadata=expected_metadata,
            actual_metadata=actual_metadata,
        )

        # If metadata_checker provided, run deterministic check as additional gate
        if metadata_checker is not None:
            metadata_passed = metadata_checker(expected_metadata, actual_metadata)
            passed = output_passed and metadata_passed
        else:
            metadata_passed = None
            passed = output_passed

        # Create result
        case_id = storage.generate_id()
        run["results"][case_id] = {
            "case_id": case_id,
            "inputs": inputs,
            "expected_outcome": expected,
            "passed": passed,
            "actual_output": output,
            "judgment": "PASS" if passed else "FAIL",
            "reasoning": reasoning,
            "expected_metadata": expected_metadata,
            "actual_metadata": actual_metadata,
            "metadata_passed": metadata_passed,
            "created_at": datetime.now().isoformat(),
        }

        # Update run
        run["status"] = "completed"
        run["passed"] = 1 if passed else 0
        run["failed"] = 0 if passed else 1
        run["score"] = 100.0 if passed else 0.0
        run["completed_at"] = datetime.now().isoformat()

        # Save run using the ad-hoc dataset ID
        saved_run = storage.save_run(self.ADHOC_DATASET_ID, run)

        return {
            "passed": passed,
            "reasoning": reasoning,
            "run_id": saved_run["filename"],
        }

    @staticmethod
    def _process_case(
        case: dict,
        agent: AgentCallable,
        judge_fn,
        metadata_checker: Optional[MetadataChecker],
    ) -> dict:
        """Process a single case. Thread-safe: no side effects.

        Args:
            case: Case dict from dataset
            agent: Agent callable
            judge_fn: Judge function
            metadata_checker: Optional metadata checker

        Returns:
            Dict with case_id, case_name, passed, and full result data.
        """
        case_id = case.get("id", storage.generate_id())
        inputs = case.get("inputs", [])
        typed_inputs = [MessageInput(**inp) for inp in inputs]

        # Call agent
        try:
            agent_result = agent(typed_inputs)
            if isinstance(agent_result, AgentResponse):
                output = agent_result.output
                actual_metadata = agent_result.metadata
            else:
                output = agent_result
                actual_metadata = None
            error_message = None
        except Exception as e:
            output = None
            actual_metadata = None
            error_message = str(e)

        # Judge
        expected_metadata = case.get("expected_metadata")

        if error_message:
            passed = False
            reasoning = f"Error: {error_message}"
            metadata_passed = None
        else:
            output_passed, reasoning = judge_fn(
                inputs,
                case.get("expected_outcome", ""),
                output,
                expected_metadata=expected_metadata,
                actual_metadata=actual_metadata,
            )
            if metadata_checker is not None:
                metadata_passed = metadata_checker(expected_metadata, actual_metadata)
                passed = output_passed and metadata_passed
            else:
                metadata_passed = None
                passed = output_passed

        return {
            "case_id": case_id,
            "case_name": case.get("name"),
            "passed": passed,
            "result": {
                "case_id": case_id,
                "passed": passed,
                "actual_output": str(output) if output else None,
                "judgment": "PASS" if passed else "FAIL",
                "reasoning": reasoning,
                "error_message": error_message,
                "expected_metadata": expected_metadata,
                "actual_metadata": actual_metadata,
                "metadata_passed": metadata_passed,
                "created_at": datetime.now().isoformat(),
                "case": {
                    "id": case_id,
                    "name": case.get("name"),
                    "inputs": inputs,
                    "expected_outcome": case.get("expected_outcome", ""),
                },
            },
        }

    def run(
        self,
        agent: AgentCallable,
        dataset: str,
        name: Optional[str] = None,
        metadata_checker: Optional[MetadataChecker] = None,
        judge_prompt: Optional[str] = None,
        case_ids: Optional[list[str]] = None,
        max_workers: Optional[int] = None,
    ) -> dict:
        """
        Run an agent against a dataset.

        Args:
            agent: Function that takes the full inputs list (list[MessageInput])
                   and returns either:
                   - str: Just the response text
                   - AgentResponse: Response with output and optional metadata
                   The inputs list contains the full conversation history,
                   allowing agents to use prior messages as context.
                   Must be thread-safe when using max_workers > 1.
            dataset: Name of the dataset to run against
            name: Optional name for this run
            metadata_checker: Optional function(expected, actual) -> bool for
                            deterministic metadata checking. If not provided,
                            metadata is passed to the LLM judge.
            judge_prompt: Custom prompt template for the judge. If not provided,
                         uses default. Available placeholders: {conversation},
                         {expected_outcome}, {expected_metadata_section},
                         {actual_output}, {actual_metadata_section}
            case_ids: Optional list of case IDs to run. If provided, only
                     matching cases are executed. If not provided, falls back
                     to BOBA_CASE_IDS environment variable (comma-separated).
            max_workers: Number of parallel workers for case execution.
                        None or <=1 means sequential. Falls back to
                        BOBA_MAX_WORKERS environment variable.

        Returns:
            dict with: passed, failed, total, score, run_id, regressions, fixes
        """
        # Load dataset
        ds = storage.get_dataset(dataset)
        if not ds:
            raise ValueError(f"Dataset '{dataset}' not found")

        dataset_id = ds["id"]
        dataset_name = ds["name"]

        cases = ds.get("cases", [])
        if not cases:
            raise ValueError(f"Dataset '{dataset}' has no cases")

        # Resolve case_ids: explicit param > env var > None (run all)
        if case_ids is None:
            env_case_ids = os.environ.get("BOBA_CASE_IDS")
            if env_case_ids:
                case_ids = [cid.strip() for cid in env_case_ids.split(",") if cid.strip()]

        # Filter to specific cases if requested
        if case_ids is not None and len(case_ids) > 0:
            available_ids = {c.get("id") for c in cases}
            unknown_ids = set(case_ids) - available_ids
            if unknown_ids:
                raise ValueError(
                    f"Case IDs not found in dataset '{dataset}': {', '.join(sorted(unknown_ids))}"
                )
            case_id_set = set(case_ids)
            cases = [c for c in cases if c.get("id") in case_id_set]

        # Resolve max_workers: explicit param > env var > None (sequential)
        if max_workers is None:
            env_workers = os.environ.get("BOBA_MAX_WORKERS")
            if env_workers:
                try:
                    max_workers = int(env_workers)
                except ValueError:
                    pass

        use_parallel = max_workers is not None and max_workers > 1

        # Create run record
        run = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "eval_name": name or f"eval-{dataset_name}",
            "status": "running",
            "total": len(cases),
            "passed": 0,
            "failed": 0,
            "started_at": datetime.now().isoformat(),
            "results": {},
        }

        # Save initial run state (using dataset ID)
        run = storage.save_run(dataset_id, run)

        # Get judge
        judge_fn = self._get_judge(prompt=judge_prompt)

        # Run cases
        passed_count = 0
        failed_count = 0

        if use_parallel:
            # Parallel execution
            lock = threading.Lock()
            save_counter = 0
            SAVE_INTERVAL = 5

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._process_case, case, agent, judge_fn, metadata_checker
                    ): case
                    for case in cases
                }

                for future in as_completed(futures):
                    result_data = future.result()
                    case_id = result_data["case_id"]

                    with lock:
                        run["results"][case_id] = result_data["result"]
                        if result_data["passed"]:
                            passed_count += 1
                        else:
                            failed_count += 1

                        run["passed"] = passed_count
                        run["failed"] = failed_count
                        save_counter += 1

                        # Print progress
                        status = "+" if result_data["passed"] else "x"
                        case_name = result_data["case_name"] or f"Case {case_id[:8]}"
                        print(f"  {status} {case_name}")

                        # Periodic save for crash recovery
                        if save_counter % SAVE_INTERVAL == 0:
                            storage.save_run(dataset_id, run)

            # Final save after all futures complete
            storage.save_run(dataset_id, run)

        else:
            # Sequential execution
            for case in cases:
                result_data = self._process_case(case, agent, judge_fn, metadata_checker)
                case_id = result_data["case_id"]

                run["results"][case_id] = result_data["result"]
                if result_data["passed"]:
                    passed_count += 1
                else:
                    failed_count += 1

                run["passed"] = passed_count
                run["failed"] = failed_count

                # Save run after each case (atomic write)
                storage.save_run(dataset_id, run)

                # Print progress
                status = "+" if result_data["passed"] else "x"
                case_name = result_data["case_name"] or f"Case {case_id[:8]}"
                print(f"  {status} {case_name}")

        # Finalize run
        run["status"] = "completed"
        run["score"] = (passed_count / len(cases) * 100) if cases else 0.0
        run["completed_at"] = datetime.now().isoformat()

        storage.save_run(dataset_id, run)

        # Compare to baseline (using dataset ID)
        baseline = storage.get_baseline(dataset_id)
        comparison = storage.compare_run_to_baseline(run, baseline)

        # Print results
        print(f"\nResults: {passed_count}/{len(cases)} passed ({run['score']:.1f}%)")

        if comparison["has_baseline"]:
            if comparison["regressions"]:
                print(f"\n  REGRESSIONS: {len(comparison['regressions'])} cases now failing")
                for case_id in comparison["regressions"][:5]:
                    result = run["results"].get(case_id, {})
                    case_name = result.get("case", {}).get("name") or case_id[:8]
                    print(f"    - {case_name}")
                if len(comparison["regressions"]) > 5:
                    print(f"    ... and {len(comparison['regressions']) - 5} more")

            if comparison["fixes"]:
                print(f"\n  FIXES: {len(comparison['fixes'])} cases now passing")
        else:
            print("\n  No baseline found. Run 'boba baseline' to save current results as baseline.")

        return {
            "passed": passed_count,
            "failed": failed_count,
            "total": len(cases),
            "score": run["score"],
            "run_id": run["filename"],
            "regressions": comparison["regressions"],
            "fixes": comparison["fixes"],
        }
