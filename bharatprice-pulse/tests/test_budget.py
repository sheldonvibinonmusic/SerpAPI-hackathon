"""
test_budget.py — BharatPrice Pulse
Tests for search budget enforcement and credit guardrails.
"""
from app.config.search_budget import SearchBudgetController


def test_budget_creation_and_limits():
    ctrl = SearchBudgetController()
    b_quick = ctrl.create_budget("test_q", "quick")
    b_std = ctrl.create_budget("test_s", "standard")
    b_deep = ctrl.create_budget("test_d", "deep")

    assert b_quick.max_allowed == 3
    assert b_std.max_allowed == 4
    assert b_deep.max_allowed == 6


def test_budget_consumption_gate():
    ctrl = SearchBudgetController()
    budget = ctrl.create_budget("test_gate", "quick")  # max 3

    assert budget.can_search is True
    assert budget.consume("engine_1") is True  # 1/3
    assert budget.consume("engine_2") is True  # 2/3
    assert budget.consume("engine_3") is True  # 3/3

    # Budget now exhausted!
    assert budget.can_search is False
    assert budget.consume("engine_4") is False  # Rejected
    assert budget.consumed == 3
    assert budget.budget_exceeded is True


def test_cache_hits_do_not_consume_budget():
    ctrl = SearchBudgetController()
    budget = ctrl.create_budget("test_cache", "standard")  # max 4

    budget.record_cache_hit("engine_cached")
    budget.record_cache_hit("engine_cached_2")

    assert budget.from_cache == 2
    assert budget.consumed == 0
    assert budget.remaining == 4
