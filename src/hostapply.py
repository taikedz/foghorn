import os
import shutil

NL = os.linesep
TAG = "tag:foghorn"

def apply_hosts(new_data_lines:list[str]):
    new_data = NL.join([f"{s}     # {TAG}" for s in new_data_lines])

    with open("/etc/hosts") as fh:
        etc_data = ''.join([s for s in fh.readlines() if not TAG in s])

    if os.path.exists("/tmp/etc-hosts"):
        if os.system("chown root:root /tmp/etc-hosts") != 0:
            raise OSError("Failed to reown")

    with open("/tmp/etc-hosts", "w") as fh:
        fh.write(etc_data)
        fh.write(f"# =========== {TAG} ========== {NL}")
        fh.write(f"# Do not remove these tags --> {TAG} {NL}")
        fh.write(f"# ----------- {TAG} ---------- {NL}")
        fh.write(new_data)

    shutil.move("/tmp/etc-hosts", "/etc/hosts")
