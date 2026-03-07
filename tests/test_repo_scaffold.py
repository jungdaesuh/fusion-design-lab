from server.environment import TASK, environment_status


def test_environment_scaffold_status() -> None:
    assert environment_status() == "scaffolded"


def test_task_budget_is_fixed() -> None:
    assert TASK["budget"] == 6
