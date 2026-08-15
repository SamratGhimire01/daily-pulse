"""Handles git add/commit/push for a single generated content file.

Uses GitPython over the existing local repository. Does not clone or
configure remotes — assumes the repo already has an 'origin' pointing at
GITHUB_REPO_URL (set up once by the user, or already present in CI).
"""

from __future__ import annotations

from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, Repo

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitManagerError(Exception):
    """Raised when a git operation fails."""


class GitManager:
    def __init__(self, repo_path: Path, author_name: str, author_email: str):
        self.repo_path = repo_path
        self.author_name = author_name
        self.author_email = author_email
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError as exc:
            raise GitManagerError(
                f"{repo_path} is not a git repository. Run 'git init' first."
            ) from exc

    def commit_and_push(self, file_path: Path, message: str, branch: str, push: bool = True) -> bool:
        """Stage, commit, and (optionally) push a single file.

        Returns True if a commit was created. Returns False if there was
        nothing to commit (e.g. file unchanged) — this is not an error.
        """
        try:
            relative = file_path.relative_to(self.repo_path)
        except ValueError:
            relative = file_path

        try:
            self.repo.index.add([str(relative)])

            if not self.repo.index.diff("HEAD") and not self._is_new_file(relative):
                logger.info("Nothing to commit for %s (no changes detected).", relative)
                return False

            with self.repo.config_writer() as cw:
                cw.set_value("user", "name", self.author_name)
                cw.set_value("user", "email", self.author_email)

            self.repo.index.commit(message)
            logger.info("Git commit created: %s", message)
        except GitCommandError as exc:
            raise GitManagerError(f"Git commit failed: {exc}") from exc

        if push:
            try:
                origin = self.repo.remote(name="origin")
                origin.push(refspec=f"HEAD:{branch}")
                logger.info("Changes pushed successfully to %s.", branch)
            except ValueError as exc:
                raise GitManagerError(
                    "No 'origin' remote configured. Run: git remote add origin <your-repo-url>"
                ) from exc
            except GitCommandError as exc:
                raise GitManagerError(
                    f"Git push failed (check GITHUB_TOKEN / SSH auth and network): {exc}"
                ) from exc

        return True

    def _is_new_file(self, relative_path: Path) -> bool:
        try:
            return str(relative_path) in [d.a_path for d in self.repo.head.commit.diff(None)]
        except Exception:
            return True
