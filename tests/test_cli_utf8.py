import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("entry", [["-m", "genesis.run"], ["scripts/launch.py"], ["scripts/preflight.py"]])
def test_cli_help_under_cp1252(entry):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env["PYTHONUTF8"] = "0"
    cmd = [sys.executable, *entry, "--help"]
    proc = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
        cwd=str(os.path.dirname(os.path.dirname(__file__))),
    )
    assert proc.returncode == 0
    expected = "Chạy một ván Genesis Zero" if entry[0] == "-m" else (
        "Chạy chế độ phản xạ" if "launch.py" in entry[0] else "chạy cả bộ test"
    )
    assert expected in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr


@pytest.mark.parametrize("module", ["scripts.launch", "scripts.preflight"])
def test_launcher_help_under_cp1252(module):
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    proc = subprocess.run(
        [sys.executable, "-m", module, "--help"], env=env,
        capture_output=True, encoding="utf-8", timeout=15,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    assert proc.returncode == 0, proc.stderr
    assert "usage:" in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr


def test_run_cli_debug_rng(capsys):
    from genesis import run

    ret = run.main(["--debug-rng", "--seed", "42"])
    assert ret == 0
    captured = capsys.readouterr()
    lines = [ln.strip() for ln in captured.out.strip().splitlines() if ln.strip()]
    assert len(lines) == run.DEBUG_RNG_SAMPLES
    # All lines should be valid floats
    for ln in lines:
        val = float(ln)
        assert 0.0 <= val <= 1.0


def test_run_cli_print_map(capsys):
    from genesis import run

    ret = run.main(["--print-map", "--seed", "1"])
    assert ret == 0
    captured = capsys.readouterr()
    lines = [ln for ln in captured.out.splitlines() if ln]
    assert len(lines) > 0


def test_run_cli_select_creatures():
    from unittest.mock import MagicMock

    from genesis.run import select_creatures

    def _mk(cid: str):
        c = MagicMock()
        c.id = cid
        return c

    cs = [_mk("L1:0"), _mk("L1:1"), _mk("L2:0")]

    assert select_creatures(None, cs) == []
    assert select_creatures("", cs) == []
    assert select_creatures("all", cs) == ["L1:0", "L1:1", "L2:0"]
    assert select_creatures("L1", cs) == ["L1:0", "L1:1"]
    assert select_creatures("L1:0, L2:0", cs) == ["L1:0", "L2:0"]

    with pytest.raises(SystemExit, match="không có sinh vật hay loài nào tên 'NON_EXISTENT'"):
        select_creatures("NON_EXISTENT", cs)


def test_run_cli_llm_and_truth(tmp_path, monkeypatch):
    from genesis import run
    from genesis.minds import Minds
    from genesis.strategist import ReflexStrategist

    class DummyLlmStrategist(ReflexStrategist):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.minds = Minds()
            self.slots = {}
            self.pending_say = {}
            self.shift_choice = {}
            self.shift_why = {}
            self.want_shift = set()

    monkeypatch.setattr("genesis.run.LlmStrategist", DummyLlmStrategist)

    truth_file = tmp_path / "truth.json"
    out_file = tmp_path / "run.jsonl"

    ret = run.main([
        "--seed", "1",
        "--ticks", "2",
        "--no-render",
        "--llm", "L1",
        "--llm-url", "http://fake-llm:8000",
        "--hunch",
        "--truth", str(truth_file),
        "--out", str(out_file),
    ])
    assert ret == 0
    assert truth_file.exists()
    assert out_file.exists()


def test_run_cli_controller_reflex(tmp_path):
    from genesis import run

    out_file = tmp_path / "run_reflex.jsonl"
    ret = run.main([
        "--seed", "1",
        "--ticks", "2",
        "--no-render",
        "--controller", "reflex",
        "--no-laws",
        "--out", str(out_file),
    ])
    assert ret == 0
    assert out_file.exists()


def test_run_cli_replay(tmp_path, monkeypatch):
    from genesis import run
    from genesis.minds import Minds
    from genesis.strategist import ReflexStrategist

    class DummyReplayStrategist(ReflexStrategist):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.minds = Minds()
            self.slots = {}
            self.pending_say = {}
            self.shift_choice = {}
            self.shift_why = {}
            self.want_shift = set()

    monkeypatch.setattr("genesis.run.LlmStrategist", DummyReplayStrategist)
    monkeypatch.setattr("genesis.run.ReplayStrategist", DummyReplayStrategist)

    replay_file = tmp_path / "fake_log.jsonl"
    replay_file.write_text('{"tick": 0, "kind": "RUN_START"}\n', encoding="utf-8")
    out_file = tmp_path / "replay_out.jsonl"

    ret = run.main([
        "--seed", "1",
        "--ticks", "2",
        "--no-render",
        "--replay", str(replay_file),
        "--out", str(out_file),
    ])
    assert ret == 0



