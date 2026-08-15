from __future__ import annotations

import pytest
from git import Repo

from src.github.git_manager import GitManager, GitManagerError


@pytest.fixture
def repo_with_local_remote(tmp_path):
    """A real local git repo with a real *local* bare remote (no network/GitHub)."""
    remote_path = tmp_path / "remote.git"
    Repo.init(remote_path, bare=True)

    work_path = tmp_path / "work"
    work_path.mkdir()
    repo = Repo.init(work_path)
    repo.create_remote("origin", str(remote_path))

    # Need an initial commit so HEAD exists before we test our add/commit flow.
    readme = work_path / "README.md"
    readme.write_text("init\n")
    repo.index.add(["README.md"])
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Setup")
        cw.set_value("user", "email", "setup@example.com")
    repo.index.commit("init")
    repo.git.branch("-M", "main")
    repo.remote("origin").push(refspec="HEAD:main")

    return work_path


def test_commit_and_push_creates_commit(repo_with_local_remote):
    manager = GitManager(repo_with_local_remote, author_name="Bot", author_email="bot@example.com")

    new_file = repo_with_local_remote / "content" / "quotes" / "2026-08-15.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_text("# Daily Quote\n")

    committed = manager.commit_and_push(new_file, message="docs: add daily quote - 2026-08-15", branch="main")

    assert committed is True
    repo = Repo(repo_with_local_remote)
    assert repo.head.commit.message == "docs: add daily quote - 2026-08-15"


def test_commit_and_push_missing_remote_raises(tmp_path):
    work_path = tmp_path / "work_no_remote"
    work_path.mkdir()
    repo = Repo.init(work_path)
    readme = work_path / "README.md"
    readme.write_text("init\n")
    repo.index.add(["README.md"])
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Setup")
        cw.set_value("user", "email", "setup@example.com")
    repo.index.commit("init")

    manager = GitManager(work_path, author_name="Bot", author_email="bot@example.com")
    new_file = work_path / "content.md"
    new_file.write_text("hello")

    with pytest.raises(GitManagerError):
        manager.commit_and_push(new_file, message="test commit", branch="main")


def test_manager_rejects_non_git_directory(tmp_path):
    not_a_repo = tmp_path / "plain_dir"
    not_a_repo.mkdir()
    with pytest.raises(GitManagerError):
        GitManager(not_a_repo, author_name="Bot", author_email="bot@example.com")
