# Logseq: [[TTA.dev/Platform_tta_dev/Components/Serena/Core/Src/Solidlsp/Util/Subprocess_util]]
import platform
import subprocess


def subprocess_kwargs():
    """
    Returns a dictionary of keyword arguments for subprocess calls, adding platform-specific
    flags that we want to use consistently.
    """
    kwargs = {}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore
    return kwargs
