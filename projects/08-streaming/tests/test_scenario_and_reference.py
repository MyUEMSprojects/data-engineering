"""Sem Kafka/Spark: o cenário e o 'gabarito' (a semântica que o job Spark precisa reproduzir)."""

from datetime import timedelta

import pytest

from streamlab.events import DELAY_S, T0, WINDOW_S, Click, Phase, build_scenario, parse_click
from streamlab.reference import expected_results, window_start


def _p(*clicks, raw=()):
    return Phase("t", [c.to_bytes() for c in clicks] + list(raw))


def _c(eid, minute, sec=0, page="home", user="u1"):
    return Click(eid, user, page, T0 + timedelta(minutes=minute, seconds=sec))


# ---------------------------------------------------------------- parse
def test_parse_roundtrip_and_rejects():
    c = _c("e1", 3, 5)
    assert parse_click(c.to_bytes()) == c
    for bad in (
        b"",
        b"{",
        b"[1]",
        b'{"event_id":"x"}',
        b'{"event_id":"x","user_id":"u","page":"","event_time":"2024-03-01T12:00:00+00:00"}',
        b'{"event_id":"x","user_id":"u","page":"p","event_time":"ontem"}',
        b'{"event_id":"x","user_id":5,"page":"p","event_time":"2024-03-01T12:00:00+00:00"}',
        None,
    ):
        assert parse_click(bad) is None


def test_window_start_floors_to_the_minute():
    assert window_start(T0 + timedelta(seconds=119, milliseconds=999)) == T0 + timedelta(minutes=1)


# ---------------------------------------------------------------- semântica de watermark
def test_nothing_is_late_in_the_first_batch_even_if_wildly_disordered():
    exp = expected_results(
        [_p(_c("a", 30), _c("b", 0))]
    )  # o min 0 chega DEPOIS do min 30, mas é o mesmo lote
    assert exp.dropped_late == 0 and len(exp.windows) == 2


def test_watermark_uses_only_PREVIOUS_batches():
    exp = expected_results([_p(_c("a", 10)), _p(_c("b", 20), _c("c", 1))])
    # fim do lote 1: max=10m ⇒ WM=8m. No lote 2, 'c' (janela 1m-2m, fim 2m ≤ 8m) é tardio; 'b' avança só o WM do lote 3
    assert exp.dropped_late == 1 and exp.watermarks[1] == T0 + timedelta(minutes=10) - timedelta(
        seconds=DELAY_S
    )


def test_late_rule_is_window_END_le_watermark():
    # WM do lote 2 = 12m − 2m = 10m
    base = _p(_c("m", 12))
    on_edge = _c("edge", 9, 0)  # janela [9m,10m): fim = 10m ≤ WM(10m) ⇒ tardio
    inside = Click("in", "u2", "home", T0 + timedelta(minutes=10))  # janela [10m,11m): fim 11m > 10m ⇒ conta
    exp = expected_results([base, _p(on_edge, inside)])
    assert exp.dropped_late == 1 and (T0 + timedelta(minutes=10), "home") in exp.windows


def test_dedup_comes_before_aggregation_and_counts_distinct_users():
    exp = expected_results(
        [_p(_c("a", 1, user="u1"), _c("a", 1, user="u1"), _c("b", 1, user="u2"), _c("c", 1, user="u1"))]
    )
    assert exp.duplicates == 1
    assert exp.windows[(T0 + timedelta(minutes=1), "home")] == (3, 2)  # 3 views, 2 usuários distintos


def test_rejects_are_counted_and_do_not_advance_the_watermark():
    exp = expected_results([_p(_c("a", 1), raw=[b"lixo"]), _p(_c("b", 1))])
    assert exp.rejects == 1 and exp.watermarks[1] == T0 + timedelta(minutes=1) - timedelta(seconds=DELAY_S)


# ---------------------------------------------------------------- o cenário
def test_scenario_is_deterministic():
    a, b = build_scenario(), build_scenario()
    assert [p.messages for p in a] == [p.messages for p in b]
    assert build_scenario(seed=8)[0].messages != a[0].messages


def test_scenario_expected_numbers():
    exp = expected_results(build_scenario())
    assert (exp.duplicates, exp.dropped_late, exp.rejects) == (15, 18, 3)
    assert sum(v for v, _ in exp.windows.values()) == 663


def test_scenario_margins_make_the_result_independent_of_micro_batch_boundaries():
    """Todo evento 'tardio' ou 'tolerado' está a ≥ 30 s do limite da regra — a decisão é inequívoca."""
    phases = build_scenario()
    exp = expected_results(phases)
    for ph, wm in zip(phases, exp.watermarks, strict=True):
        if wm is None:
            continue
        for raw in ph.messages:
            c = parse_click(raw)
            if c is None:
                continue
            end = window_start(c.event_time) + timedelta(seconds=WINDOW_S)
            if end <= wm + timedelta(seconds=WINDOW_S * 3):  # candidatos a "tardios/tolerados"
                assert abs((end - wm).total_seconds()) >= 30 or end > wm + timedelta(seconds=WINDOW_S * 2), (
                    c,
                    wm,
                )


def test_scenario_has_all_the_hard_cases():
    ph = build_scenario()
    assert [len(p.messages) for p in ph] == [412, 181, 106]
    assert ph[1].late_tolerated == 15 and ph[2].late_tolerated == 8 and ph[2].too_late == 18
    flat = [m for p in ph for m in p.messages]
    assert len(flat) != len(set(flat))  # há mensagens repetidas (at-least-once)
    assert any(parse_click(m) is None for m in flat)  # e mensagens inválidas


@pytest.mark.parametrize("n", [1, 2, 3])
def test_every_phase_has_traffic(n):
    assert build_scenario()[n - 1].messages
