# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unsafe manual versions must not become a contribs dispatch output."""

import subprocess
from pathlib import Path

import yaml

_WORKFLOW = (
    Path(__file__).resolve().parents[2] / ".github/workflows/dispatch-to-contribs.yml"
)


def test_newline_in_manual_version_writes_no_output(tmp_path):
    """A newline in the manual version must fail before any step output is written."""
    steps = {
        step["name"]: step
        for step in yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"][
            "dispatch"
        ]["steps"]
    }
    output = tmp_path / "github_output"
    output.write_text("", encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-eo",
            "pipefail",
            "-c",
            steps["Resolve version"]["run"],
        ],
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "GITHUB_OUTPUT": str(output),
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "INPUT_VERSION": "1.2.3\nfoo=bar",
        },
    )
    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == ""
    assert result.stdout == "::error::Invalid version; expected format X.Y.Z\n"
    dispatch = steps["Dispatch to mellea-contribs"]["run"]
    assert "--raw-field event_type=mellea-released" in dispatch
    assert '--raw-field "client_payload[version]=${VERSION}"' in dispatch
    assert "--field" not in dispatch
