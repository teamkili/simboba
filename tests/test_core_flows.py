"""Tests for core simboba flows."""


class TestUIServing:
    """Test that the UI is served correctly."""

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_index_serves_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "simboba" in response.text.lower()


class TestDatasetManagement:
    """Test dataset CRUD operations."""

    def test_create_dataset(self, client):
        response = client.post(
            "/api/datasets",
            json={"name": "my-dataset", "description": "Test dataset"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "my-dataset"
        assert data["description"] == "Test dataset"
        assert data["id"] is not None
        assert data["case_count"] == 0

    def test_list_datasets(self, client):
        # Create two datasets
        client.post("/api/datasets", json={"name": "dataset-1"})
        client.post("/api/datasets", json={"name": "dataset-2"})

        response = client.get("/api/datasets")
        assert response.status_code == 200
        datasets = response.json()
        assert len(datasets) == 2

    def test_get_dataset(self, client):
        create_resp = client.post("/api/datasets", json={"name": "test"})
        dataset_id = create_resp.json()["id"]

        response = client.get(f"/api/datasets/{dataset_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "test"

    def test_delete_dataset(self, client):
        create_resp = client.post("/api/datasets", json={"name": "to-delete"})
        dataset_id = create_resp.json()["id"]

        response = client.delete(f"/api/datasets/{dataset_id}")
        assert response.status_code == 200

        # Verify it's gone
        get_resp = client.get(f"/api/datasets/{dataset_id}")
        assert get_resp.status_code == 404

    def test_duplicate_name_rejected(self, client):
        client.post("/api/datasets", json={"name": "unique-name"})
        response = client.post("/api/datasets", json={"name": "unique-name"})
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestCaseManagement:
    """Test eval case CRUD operations."""

    def test_create_case(self, client):
        # First create a dataset
        ds_resp = client.post("/api/datasets", json={"name": "test-ds"})
        dataset_id = ds_resp.json()["id"]

        # Create a case
        response = client.post(
            "/api/cases",
            json={
                "dataset_id": dataset_id,
                "name": "Basic test",
                "inputs": [
                    {"role": "user", "message": "Hello", "attachments": []},
                    {"role": "assistant", "message": "Hi there", "attachments": []},
                ],
                "expected_outcome": "Agent greets the user politely",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Basic test"
        assert len(data["inputs"]) == 2
        assert data["expected_outcome"] == "Agent greets the user politely"

    def test_list_cases_by_dataset(self, client):
        # Create dataset and cases
        ds_resp = client.post("/api/datasets", json={"name": "ds"})
        dataset_id = ds_resp.json()["id"]

        for i in range(3):
            client.post(
                "/api/cases",
                json={
                    "dataset_id": dataset_id,
                    "name": f"Case {i}",
                    "inputs": [{"role": "user", "message": "test", "attachments": []}],
                    "expected_outcome": "test",
                },
            )

        response = client.get(f"/api/cases?dataset_id={dataset_id}")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_update_case(self, client):
        ds_resp = client.post("/api/datasets", json={"name": "ds"})
        dataset_id = ds_resp.json()["id"]

        case_resp = client.post(
            "/api/cases",
            json={
                "dataset_id": dataset_id,
                "name": "Original",
                "inputs": [{"role": "user", "message": "Hi", "attachments": []}],
                "expected_outcome": "Original outcome",
            },
        )
        case_id = case_resp.json()["id"]

        response = client.put(
            f"/api/cases/{case_id}",
            json={"name": "Updated", "expected_outcome": "Updated outcome"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
        assert response.json()["expected_outcome"] == "Updated outcome"

    def test_delete_case(self, client):
        ds_resp = client.post("/api/datasets", json={"name": "ds"})
        dataset_id = ds_resp.json()["id"]

        case_resp = client.post(
            "/api/cases",
            json={
                "dataset_id": dataset_id,
                "inputs": [{"role": "user", "message": "Hi", "attachments": []}],
                "expected_outcome": "test",
            },
        )
        case_id = case_resp.json()["id"]

        response = client.delete(f"/api/cases/{case_id}")
        assert response.status_code == 200

        get_resp = client.get(f"/api/cases/{case_id}")
        assert get_resp.status_code == 404


class TestExportImport:
    """Test dataset export and import."""

    def test_export_dataset(self, client):
        ds_resp = client.post("/api/datasets", json={"name": "export-test"})
        dataset_id = ds_resp.json()["id"]

        client.post(
            "/api/cases",
            json={
                "dataset_id": dataset_id,
                "name": "Case 1",
                "inputs": [{"role": "user", "message": "Hello", "attachments": []}],
                "expected_outcome": "Greet back",
            },
        )

        response = client.get(f"/api/datasets/{dataset_id}/export")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "export-test"
        assert len(data["cases"]) == 1

    def test_import_dataset(self, client):
        response = client.post(
            "/api/datasets/import",
            json={
                "name": "imported-dataset",
                "description": "Imported from JSON",
                "cases": [
                    {
                        "name": "Imported case",
                        "inputs": [
                            {"role": "user", "message": "Test", "attachments": []}
                        ],
                        "expected_outcome": "Test outcome",
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "imported-dataset"
        assert data["case_count"] == 1


class TestEvalClass:
    """Test the Eval class for running evaluations."""

    def test_eval_basic_run(self):
        from simboba import Eval

        def my_function(messages):
            return f"Received {len(messages)} messages"

        eval_config = Eval(name="test-eval", fn=my_function)

        result = eval_config.run(
            [
                {"role": "user", "message": "Hello"},
                {"role": "assistant", "message": "Hi"},
            ]
        )
        assert result == "Received 2 messages"

    def test_eval_with_transforms(self):
        from simboba import Eval

        def my_function(text):
            return {"response": text.upper()}

        def transform_inputs(messages):
            return {"text": messages[0]["message"]}

        def transform_output(result):
            return result["response"]

        eval_config = Eval(
            name="transform-eval",
            fn=my_function,
            transform_inputs=transform_inputs,
            transform_output=transform_output,
        )

        result = eval_config.run([{"role": "user", "message": "hello"}])
        assert result == "HELLO"


class TestRunner:
    """Test the eval runner module."""

    def test_run_case_success(self):
        from simboba import Eval
        from simboba.runner import run_case

        def echo_fn(messages):
            return f"Echo: {messages[0]['message']}"

        eval_config = Eval(name="echo", fn=echo_fn)
        case = {
            "id": 1,
            "inputs": [{"role": "user", "message": "Hello"}],
            "expected_outcome": "Should echo the message",
        }

        result = run_case(eval_config, case)
        assert result.case_id == 1
        assert result.actual_output == "Echo: Hello"
        assert result.execution_time_ms is not None

    def test_run_case_with_judge(self):
        from simboba import Eval
        from simboba.runner import run_case

        def greet_fn(messages):
            return "Hello there!"

        def mock_judge(inputs, expected, actual):
            return True, "Output contains greeting"

        eval_config = Eval(name="greet", fn=greet_fn)
        case = {
            "id": 1,
            "inputs": [{"role": "user", "message": "Hi"}],
            "expected_outcome": "Should greet",
        }

        result = run_case(eval_config, case, mock_judge)
        assert result.passed is True
        assert result.judgment == "PASS"
        assert result.reasoning == "Output contains greeting"

    def test_run_case_error_handling(self):
        from simboba import Eval
        from simboba.runner import run_case

        def failing_fn(messages):
            raise ValueError("Something went wrong")

        eval_config = Eval(name="fail", fn=failing_fn)
        case = {
            "id": 1,
            "inputs": [{"role": "user", "message": "Hi"}],
            "expected_outcome": "Should work",
        }

        result = run_case(eval_config, case)
        assert result.passed is False
        assert "Something went wrong" in result.error_message

    def test_run_eval_multiple_cases(self):
        from simboba import Eval
        from simboba.runner import run_eval

        def length_fn(messages):
            return f"Length: {len(messages)}"

        def mock_judge(inputs, expected, actual):
            return "Length:" in actual, "Has length"

        eval_config = Eval(name="length", fn=length_fn)
        cases = [
            {"id": 1, "inputs": [{"role": "user", "message": "A"}], "expected_outcome": "test"},
            {"id": 2, "inputs": [{"role": "user", "message": "B"}], "expected_outcome": "test"},
            {"id": 3, "inputs": [{"role": "user", "message": "C"}], "expected_outcome": "test"},
        ]

        result = run_eval(eval_config, cases, mock_judge)
        assert result.total == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.score == 100.0


class TestJudge:
    """Test the judge module."""

    def test_simple_judge_pass(self):
        from simboba.judge import create_simple_judge

        judge = create_simple_judge()
        inputs = [{"role": "user", "message": "Book appointment"}]
        expected = "Agent should book appointment"
        actual = "I have booked your appointment for tomorrow"

        passed, reasoning = judge(inputs, expected, actual)
        assert passed is True
        assert "expected terms" in reasoning.lower()

    def test_simple_judge_fail(self):
        from simboba.judge import create_simple_judge

        judge = create_simple_judge()
        inputs = [{"role": "user", "message": "Book appointment"}]
        expected = "Agent should book appointment and confirm time"
        actual = "Hello there!"

        passed, reasoning = judge(inputs, expected, actual)
        assert passed is False


class TestEvalRunAPI:
    """Test the eval run API endpoints."""

    def test_list_evals_empty(self, client):
        response = client.get("/api/evals")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_runs_empty(self, client):
        ds_resp = client.post("/api/datasets", json={"name": "ds"})
        dataset_id = ds_resp.json()["id"]

        response = client.get(f"/api/runs?dataset_id={dataset_id}")
        assert response.status_code == 200
        assert response.json() == []

    def test_start_run_no_eval_loaded(self, client):
        ds_resp = client.post("/api/datasets", json={"name": "ds"})
        dataset_id = ds_resp.json()["id"]

        # Add a case
        client.post(
            "/api/cases",
            json={
                "dataset_id": dataset_id,
                "inputs": [{"role": "user", "message": "Hi", "attachments": []}],
                "expected_outcome": "test",
            },
        )

        response = client.post(
            "/api/runs",
            json={"dataset_id": dataset_id, "eval_name": "nonexistent"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_start_run_no_cases(self, client):
        from simboba import Eval
        from simboba.server import set_loaded_evals

        # Set up a mock eval
        def mock_fn(messages):
            return "ok"

        set_loaded_evals({"test-eval": Eval(name="test-eval", fn=mock_fn)})

        ds_resp = client.post("/api/datasets", json={"name": "empty-ds"})
        dataset_id = ds_resp.json()["id"]

        response = client.post(
            "/api/runs",
            json={"dataset_id": dataset_id, "eval_name": "test-eval"},
        )
        assert response.status_code == 400
        assert "no cases" in response.json()["detail"].lower()

        # Clean up
        set_loaded_evals({})

    def test_full_run_flow(self, client):
        from simboba import Eval
        from simboba.server import set_loaded_evals

        # Set up a mock eval
        def echo_fn(messages):
            return f"Echo: {messages[0]['message']}"

        set_loaded_evals({"echo-eval": Eval(name="echo-eval", fn=echo_fn)})

        # Create dataset with cases
        ds_resp = client.post("/api/datasets", json={"name": "run-test"})
        dataset_id = ds_resp.json()["id"]

        for i in range(2):
            client.post(
                "/api/cases",
                json={
                    "dataset_id": dataset_id,
                    "name": f"Case {i}",
                    "inputs": [{"role": "user", "message": f"Test {i}", "attachments": []}],
                    "expected_outcome": "Should echo",
                },
            )

        # Start run
        run_resp = client.post(
            "/api/runs",
            json={"dataset_id": dataset_id, "eval_name": "echo-eval"},
        )
        assert run_resp.status_code == 200
        run = run_resp.json()
        assert run["status"] == "completed"
        assert run["total"] == 2
        assert run["eval_name"] == "echo-eval"

        # Get run details
        run_id = run["id"]
        detail_resp = client.get(f"/api/runs/{run_id}")
        assert detail_resp.status_code == 200
        details = detail_resp.json()
        assert len(details["results"]) == 2
        assert all("Echo:" in r["actual_output"] for r in details["results"])

        # List runs
        list_resp = client.get(f"/api/runs?dataset_id={dataset_id}")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        # Delete run
        del_resp = client.delete(f"/api/runs/{run_id}")
        assert del_resp.status_code == 200

        # Clean up
        set_loaded_evals({})
