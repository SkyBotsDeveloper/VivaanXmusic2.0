import asyncio
import os
import shlex
import socket
from typing import Optional, Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import config

from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(install_requirements())


def _is_heroku() -> bool:
    return bool(os.getenv("DYNO")) or "heroku" in socket.getfqdn().lower()


def _upstream_repo_url() -> Optional[str]:
    REPO_LINK = config.UPSTREAM_REPO
    if not REPO_LINK:
        return None
    if config.GIT_TOKEN:
        try:
            GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
            TEMP_REPO = REPO_LINK.split("https://")[1]
            return f"https://{GIT_USERNAME}:{config.GIT_TOKEN}@{TEMP_REPO}"
        except IndexError:
            LOGGER(__name__).warning("Could not add GIT_TOKEN to UPSTREAM_REPO URL.")
    return REPO_LINK


def _get_remote_ref(origin, branch):
    for ref in origin.refs:
        if getattr(ref, "remote_head", None) == branch:
            return ref
    return None


def git():
    UPSTREAM_REPO = _upstream_repo_url()
    try:
        Repo(search_parent_directories=True)
        LOGGER(__name__).info(f"Git Client Found [VPS DEPLOYER]")
        return
    except GitCommandError as err:
        LOGGER(__name__).warning(f"Invalid Git Command: {err}")
        return
    except InvalidGitRepositoryError:
        if _is_heroku():
            LOGGER(__name__).info(
                "No Git repository found on Heroku dyno; skipping startup git sync."
            )
            return
        if not UPSTREAM_REPO:
            LOGGER(__name__).warning(
                "UPSTREAM_REPO is not configured; skipping startup git sync."
            )
            return

        repo = Repo.init()
        try:
            origin = repo.remote("origin")
        except ValueError:
            origin = repo.create_remote("origin", UPSTREAM_REPO)

        try:
            origin.set_url(UPSTREAM_REPO)
            origin.fetch(config.UPSTREAM_BRANCH)
            remote_ref = _get_remote_ref(origin, config.UPSTREAM_BRANCH)
            if remote_ref is None:
                LOGGER(__name__).warning(
                    f"Upstream branch '{config.UPSTREAM_BRANCH}' was not found; "
                    "skipping startup git sync."
                )
                return
            if config.UPSTREAM_BRANCH in repo.heads:
                branch = repo.heads[config.UPSTREAM_BRANCH]
            else:
                branch = repo.create_head(config.UPSTREAM_BRANCH, remote_ref)
            branch.set_tracking_branch(remote_ref)
            branch.checkout(force=True)
            repo.git.reset("--hard", remote_ref.path)
            install_req("pip3 install --no-cache-dir -r requirements.txt")
            LOGGER(__name__).info(f"Fetching updates from upstream repository...")
        except GitCommandError as err:
            LOGGER(__name__).warning(f"Startup git sync failed: {err}")
