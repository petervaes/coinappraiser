import os

from coinappraiser.config import load_environment


def test_load_environment_reads_nearest_env_file_without_overriding(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / ".env").write_text(
        "COINAPPR_TEST_FROM_FILE=file-value\n"
        "COINAPPR_TEST_PRECEDENCE=file-value\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("COINAPPR_TEST_FROM_FILE", raising=False)
    monkeypatch.setenv("COINAPPR_TEST_PRECEDENCE", "existing-value")

    load_environment()

    assert os.environ["COINAPPR_TEST_FROM_FILE"] == "file-value"
    assert os.environ["COINAPPR_TEST_PRECEDENCE"] == "existing-value"
