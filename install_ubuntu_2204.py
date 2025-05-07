#!/usr/bin/env python3
# https://www.baeldung.com/linux/curl-fetched-script-arguments
import json
import shutil
import subprocess
import tempfile
import pathlib
from getpass import getpass, getuser
from typing import Tuple


# Requirements:
# - python3
# - curl
# - sudo
# Usage:
# python3 <(curl --silent https://raw.githubusercontent.com/michimussato/OpenStudioLandscapes-Temp/refs/heads/main/install_ubuntu_2204.py)


def _get_terminal_size() -> Tuple[int, int]:
    # https://stackoverflow.com/a/14422538
    cols, rows = shutil.get_terminal_size((80, 20))
    return cols, rows


def sudo_pass() -> bytes:
    print(" ENTER PASSWORD ".center(_get_terminal_size()[0], "#"))
    _sudo_pass = getpass(prompt=f"Sudo Password for User {getuser()}: ")
    return _sudo_pass.encode()


def script_run(
    sudo: bool = False,
    *,
    script: pathlib.Path,
) -> tuple[bytes, bytes]:

    cmd = [
        shutil.which("bash"),
        script.as_posix(),
    ]

    if sudo:
        cmd.insert(0, shutil.which("sudo"))
        cmd.insert(1, "--stdin")

    proc = subprocess.run(
        cmd,
        input=None if not sudo else sudo_pass(),
        check=True,
        # cwd=script_prep.parent.as_posix(),
        # env=os.environ,
    )

    if proc.returncode:
        raise RuntimeError(proc)

    return proc.stdout, proc.stderr


def script_disable_unattended_upgrades() -> pathlib.Path:
    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "sudo systemctl disable --now unattended-upgrades\n",
            ]
        )

        return pathlib.Path(script.name)


def script_prep() -> pathlib.Path:
    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "sudo apt-get update\n",
                "sudo apt-get upgrade -y\n",
                "\n",
                "sudo apt-get install -y openssh-server\n",
                "sudo apt-get install -y git\n",
                "sudo apt-get install -y htop\n",
                "sudo apt-get install -y vim\n",
                "\n",
                "sudo apt-get -y autoremove\n",
                "sudo apt-get clean\n",
                "\n",
                "sudo systemctl enable --now ssh\n",
            ]
        )

        return pathlib.Path(script.name)


def script_clone_openstudiolandscapes(
    ssh_key_file: pathlib.Path = pathlib.Path("~/.ssh/id_ed25519").expanduser(),
    known_hosts_file: pathlib.Path = pathlib.Path("~/.ssh/known_hosts").expanduser(),
    openstudiolandscapes_repo_dir: pathlib.Path = pathlib.Path("~/git/repos/OpenStudioLandscapes").expanduser(),
) -> pathlib.Path:

    print(" ENTER EMAIL ".center(_get_terminal_size()[0], "#"))
    print("Enter your email: ")
    email = input()

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                # f"{shutil.which('ssh-keygen')}\n",
                f"ssh-keygen -f {ssh_key_file.as_posix()} -N '' -t ed25519 -C \"{email}\"\n",
                "eval \"$(ssh-agent -s)\"\n",
                f"ssh-add {ssh_key_file.as_posix()}\n",
                "\n",
                "echo \"Copy/Paste the following Public Key to GitHub:\"\n",
                "echo \"https://github.com/settings/ssh/new\"\n",
                f"cat {ssh_key_file.as_posix()}.pub\n",
                "\n",
                "while [[ \"$choice_ssh\" != [Yy]* ]]; do\n",
                "    read -r -e -p \"Type [Yy]es when ready... \" choice_ssh\n",
                "done\n",
                "\n",
                f"ssh-keyscan github.com >> {known_hosts_file.as_posix()}\n",
                "\n",
                f"mkdir -p {openstudiolandscapes_repo_dir.as_posix()}\n",
                f"git -C {openstudiolandscapes_repo_dir.parent.as_posix()} clone git@github.com:michimussato/OpenStudioLandscapes.git\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_python(
    PYTHON_MAJ: int = 3,
    PYTHON_MIN: int = 11,
    PYTHON_PAT: int = 11,
) -> pathlib.Path:
    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "while ! sudo apt-get upgrade -y; then\n",
                "sudo apt-get upgrade -y\n",
                "    echo \"Update in progress in the background...\"\n",
                "    sleep 5\n",
                "done;\n",
                "\n",
                "sudo apt-get install -y build-essential\n",
                "sudo apt-get install -y zlib1g-dev\n",
                "sudo apt-get install -y libncurses5-dev\n",
                "sudo apt-get install -y libgdbm-dev\n",
                "sudo apt-get install -y libnss3-dev\n",
                "sudo apt-get install -y libssl-dev\n",
                "sudo apt-get install -y libreadline-dev\n",
                "sudo apt-get install -y libffi-dev\n",
                "sudo apt-get install -y wget\n",
                "sudo apt-get install -y pkg-config\n",
                "sudo apt-get install -y liblzma-dev\n",
                "sudo apt-get install -y libbz2-dev\n",
                "sudo apt-get install -y curl\n",
                "\n",
                "pushd \"$(mktemp -d)\" || exit\n",
                "\n",
                f"curl \"https://www.python.org/ftp/python/{PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT}/Python-{PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT}.tgz\" -o Python-{PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT}.tgz\n",
                f"tar -xvf Python-{PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT}.tgz\n",
                f"cd Python-{PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT} || exit\n",
                "\n",
                "./configure --enable-optimizations\n",
                "make -j \"$(nproc)\"\n",
                "sudo make altinstall\n",
                "\n",
                "popd || exit\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_docker(
    docker_user: str,
    edit_docker_daemon_json: bool = True,
    url_harbor: str = "http://harbor.farm.evil:80",
) -> pathlib.Path:
    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "# Documentation:\n",
                "# https://docs.docker.com/engine/install/ubuntu/\n",
                "\n",
                "for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do\n",
                "    sudo apt-get remove $pkg\n",
                "done\n",
                "\n",
                "sudo apt autoremove -y\n",
                "\n",
                "sudo apt-get update\n",
                "\n",
                "sudo apt-get install -y ca-certificates\n",
                "sudo apt-get install -y curl\n",
                "\n",
                "sudo install -m 0755 -d /etc/apt/keyrings\n",
                "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc\n",
                "sudo chmod a+r /etc/apt/keyrings/docker.asc\n",
            ]
        )

        if edit_docker_daemon_json:

            daemon_json = {
                "insecure-registries" : [
                    url_harbor,
                ],
                "max-concurrent-uploads": 1,
            }

            daemon_json_ = json.dumps(daemon_json, indent=2)

            script.writelines(
                [
                    "\n",
                    "sudo -s << EOF\n",
                    "mkdir -p /etc/docker\n",
                    "touch /etc/docker/daemon.json\n",
                    "cat > /etc/docker/daemon.json\n",
                    f"{daemon_json_}\n",
                    "EOF\n",
                    "echo\"Your /etc/docker/daemon.json file looks like:\"\n",
                    "cat /etc/docker/daemon.json\n",
                ]
            )

        script.writelines(
            [
                "\n",
                "echo \\\n",
                "  \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \\\n",
                "  $(. /etc/os-release && echo \"${UBUNTU_CODENAME:-$VERSION_CODENAME}\") stable\" | \\\n",
                "  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null\n",
                "sudo apt-get update\n",
                "\n",
                "sudo apt-get install -y docker-ce\n",
                "sudo apt-get install -y docker-ce-cli\n",
                "sudo apt-get install -y containerd.io\n",
                "sudo apt-get install -y docker-buildx-plugin\n",
                "sudo apt-get install -y docker-compose-plugin\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "# https://docs.docker.com/engine/install/linux-postinstall/\n",
                "\n",
                "sudo groupadd --force docker\n",
                f"sudo usermod --append --groups docker \"{docker_user}\"\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "sudo systemctl daemon-reload\n",
                "sudo systemctl restart docker\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_openstudiolandscapes(
    openstudiolandscapes_repo_dir: pathlib.Path = pathlib.Path("~/git/repos/OpenStudioLandscapes").expanduser(),
) -> pathlib.Path:

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "sudo apt-get install -y graphviz\n",
                "\n",
                f"cd {openstudiolandscapes_repo_dir.as_posix()}\n",
                f"{shutil.which('python3.11')} -m venv .venv\n",
                "\n",
                "source .venv/bin/activate\n",
                "pip install --upgrade pip setuptools setuptools_scm wheel\n",
                "\n",
                "pip install -e .[dev]\n",
                "\n",
                "nox -s clone_features\n",
                "nox -s install_features_into_engine\n",
                "\n",
                "deactivate\n",
            ]
        )

        return pathlib.Path(script.name)


def script_etc_hosts() -> pathlib.Path:

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "for fqdn in \\\n",
                "    dagster.farm.evil \\\n",
                "    postgres-dagster.farm.evil \\\n",
                "    harbor.farm.evil \\\n",
                "    pi-hole.farm.evil \\\n",
                "; do \n",
                "    sed -i -e \"\$a127.0.0.1    $fqdn\" -e \"/127.0.0.1    ${fqdn}/d\" /etc/hosts\n",
                "done\n",
                "\n",
                "echo\"Your /etc/hosts file looks like:\"\n",
                "cat /etc/hosts\n",
            ]
        )

        return pathlib.Path(script.name)


def script_init_harbor(
    openstudiolandscapes_repo_dir: pathlib.Path = pathlib.Path("~/git/repos/OpenStudioLandscapes").expanduser(),
) -> pathlib.Path:

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                f"cd {openstudiolandscapes_repo_dir.as_posix()}\n",
                "source .venv/bin/activate\n",
                "nox --session harbor_prepare\n",
                "deactivate\n",
            ]
        )

        return pathlib.Path(script.name)


def script_init_pihole(
    openstudiolandscapes_repo_dir: pathlib.Path = pathlib.Path("~/git/repos/OpenStudioLandscapes").expanduser(),
) -> pathlib.Path:

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                f"cd {openstudiolandscapes_repo_dir.as_posix()}\n",
                "source .venv/bin/activate\n",
                "nox --session pi_hole_prepare\n",
                "deactivate\n",
            ]
        )

        return pathlib.Path(script.name)


def script_reboot() -> pathlib.Path:

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                f"{shutil.which('systemctl')} reboot\n",
            ]
        )

        return pathlib.Path(script.name)


if __name__ == "__main__":

    ret_script_disable_unattended_upgrades = script_run(
        sudo=True,
        script=script_disable_unattended_upgrades(),
    )
    ret_script_prep = script_run(
        sudo=True,
        script=script_prep(),
    )
    ret_script_clone_openstudiolandscapes = script_run(
        sudo=False,
        script=script_clone_openstudiolandscapes(),
    )
    ret_script_install_python = script_run(
        sudo=True,
        script=script_install_python(),
    )
    ret_script_install_docker = script_run(
        sudo=True,
        script=script_install_docker(
            docker_user=getuser(),
        ),
    )
    ret_script_install_openstudiolandscapes = script_run(
        sudo=True,
        script=script_install_openstudiolandscapes(),
    )
    ret_script_etc_hosts = script_run(
        sudo=True,
        script=script_etc_hosts(),
    )
    ret_script_init_harbor = script_run(
        sudo=True,
        script=script_init_harbor(),
    )
    ret_script_init_pihole = script_run(
        sudo=False,
        script=script_init_pihole(),
    )
    script_reboot()
