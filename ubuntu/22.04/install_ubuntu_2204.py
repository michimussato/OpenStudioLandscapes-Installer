#!/usr/bin/env python3
# https://www.baeldung.com/linux/curl-fetched-script-arguments
import base64
import json
import shlex
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
# python3 <(curl --header 'Cache-Control: no-cache, no-store' --silent https://raw.githubusercontent.com/michimussato/OpenStudioLandscapes-Temp/refs/heads/main/ubuntu/22.04/install_ubuntu_2204.py)


OPENSTUDIOLANDSCAPES_DIR: pathlib.Path = pathlib.Path("~/git/repos/OpenStudioLandscapes").expanduser()
URL_HARBOR: str = "http://harbor.farm.evil:80"
ADMIN_HARBOR: str = "admin"
PASSWORD_HARBOR: str = "Harbor12345"


def _get_terminal_size() -> Tuple[int, int]:
    # https://stackoverflow.com/a/14422538
    # https://stackoverflow.com/a/18243550
    cols, rows = shutil.get_terminal_size((80, 20))
    return cols, rows


def sudo_pass() -> bytes:
    print(" ENTER PASSWORD ".center(_get_terminal_size()[0], "="))
    _sudo_pass = getpass(prompt=f"Sudo Password for User `{getuser()}`: ")
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

    with open(script.as_posix(), "r") as f:
        lines = f.readlines()
        print(" COMMAND ".center(_get_terminal_size()[0], "-"))
        print(f" {shlex.join(cmd)} ".center(_get_terminal_size()[0], " "))
        print(" SCRIPT START ".center(_get_terminal_size()[0], "-"))
        lno = 0
        len_ = len(str(len(lines)))
        for l in lines:
            lno += 1
            print(f"{str(lno).ljust(len_)}: {l.rstrip()}")
        print(" SCRIPT END ".center(_get_terminal_size()[0], "-"))

    try:
        proc = subprocess.run(
            cmd,
            input=None if not sudo else sudo_pass(),
            check=True,
            # cwd=script_prep.parent.as_posix(),
            # env=os.environ,
        )
    except subprocess.CalledProcessError as e:
        print(cmd)
        # with open(script.as_posix(), "r") as f:
        #     print(f.read())
        raise e

    if proc.returncode:
        raise RuntimeError(proc)

    return proc.stdout, proc.stderr


def script_disable_unattended_upgrades() -> pathlib.Path:
    print(" DISABLE UNATTENDED UPGRADES ".center(_get_terminal_size()[0], "#"))
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

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_prep() -> pathlib.Path:
    print(" PREP ".center(_get_terminal_size()[0], "#"))
    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:

        prep_pkgs = [
            "openssh-server",
            "git",
            "htop",
            "vim",
            "graphviz",
        ]
        script.writelines(
            [
                "#!/bin/env bash\n",
                "\n",
                "\n",
                "sudo apt-get update\n",
                "sudo apt-get upgrade -y\n",
                "\n",
                f"sudo apt-get install --no-install-recommends -y {' '.join(prep_pkgs)}\n",
                "\n",
                "sudo apt-get -y autoremove\n",
                "sudo apt-get clean\n",
                "\n",
                "sudo systemctl enable --now ssh\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_clone_openstudiolandscapes(
    ssh_key_file: pathlib.Path = pathlib.Path("~/.ssh/id_ed25519").expanduser(),
    known_hosts_file: pathlib.Path = pathlib.Path("~/.ssh/known_hosts").expanduser(),
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    # Todo
    #  - [ ] We *could* add some checks here in case git clone fails.
    #        However, ssh authentication is only necessary while repo
    #        private.
    #  - [ ] git clone fails silently if ~/git/repos/OpenStudioLandscapes
    #        already exists. FIX!

    print(" CLONE OPENSTUDIOLANDSCAPES ".center(_get_terminal_size()[0], "#"))

    print(" ENTER EMAIL ".center(_get_terminal_size()[0], "="))
    email = input("Enter your email: ")

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
            ]
        )

        # If openstudiolandscapes_repo_dir already exists, we move it out
        # of the way. At least until there is a more finegrained solution
        # in place to deal with existing installations.
        script.writelines(
            [
                "\n",
                f"if [ -d {openstudiolandscapes_repo_dir.as_posix()} ]; then\n",
                f"    mv {openstudiolandscapes_repo_dir.as_posix()} {openstudiolandscapes_repo_dir.as_posix()}_$(date +\"%Y-%m-%d_%H-%m-%S\")\n",
                "fi\n",
            ]
        )

        script.writelines(
            [
                "\n",
                f"if [ ! -d {openstudiolandscapes_repo_dir.as_posix()} ]; then\n",
                f"    mkdir -p {openstudiolandscapes_repo_dir.as_posix()}\n",
                "fi\n",
                f"git -C {openstudiolandscapes_repo_dir.parent.as_posix()} clone --tags git@github.com:michimussato/OpenStudioLandscapes.git\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_python(
    PYTHON_MAJ: int = 3,
    PYTHON_MIN: int = 11,
    PYTHON_PAT: int = 11,
) -> pathlib.Path:

    print(f" INSTALL PYTHON {PYTHON_MAJ}.{PYTHON_MIN}.{PYTHON_PAT}".center(_get_terminal_size()[0], "#"))

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
            ],
        )

        script.writelines(
            [
                f"if which python3.11; then\n",
                "    echo \"python3.11 is already installed\"\n",
                "    exit 0\n",
                "fi\n",
                "\n",
                "\n",
            ]
        )

        python_pkgs = [
            "build-essential",
            "zlib1g-dev",
            "libncurses5-dev",
            "libgdbm-dev",
            "libnss3-dev",
            "libssl-dev",
            "libreadline-dev",
            "libffi-dev",
            "wget",
            "pkg-config",
            "liblzma-dev",
            "libbz2-dev",
            "libsqlite3-dev",
            "curl",
        ]
        script.writelines(
            [
                # line 10: [: too many arguments
                "while [ ! sudo apt-get upgrade -y ]; do\n",
                "    echo \"Update in progress in the background...\"\n",
                "    sleep 5\n",
                "done;\n",
                "\n",
                f"sudo apt-get install --no-install-recommends -y {' '.join(python_pkgs)}\n",
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

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_docker(
    docker_user: str,
    edit_docker_daemon_json: bool = True,
    url_harbor: str = URL_HARBOR,
) -> pathlib.Path:

    print(" INSTALL DOCKER ".center(_get_terminal_size()[0], "#"))

    with tempfile.NamedTemporaryFile(
            delete=False,
            encoding="utf-8",
            prefix="ubuntu_2204_",
            suffix=".sh",
            mode="x",
    ) as script:
        docker1_pkgs = [
            "ca-certificates",
            "curl",
        ]
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
                f"sudo apt-get install --no-install-recommends -y {' '.join(docker1_pkgs)}\n",
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
                ]
            )

        docker_pkgs = [
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ]
        script.writelines(
            [
                "\n",
                "echo \\\n",
                "  \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \\\n",
                "  $(. /etc/os-release && echo \"${UBUNTU_CODENAME:-$VERSION_CODENAME}\") stable\" | \\\n",
                "  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null\n",
                "sudo apt-get update\n",
                "\n",
                f"sudo apt-get install --no-install-recommends -y {' '.join(docker_pkgs)}\n",
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

        script.writelines(
            [
                "\n",
                "echo \"Your /etc/docker/daemon.json file looks like:\"\n",
                "cat /etc/docker/daemon.json\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_install_openstudiolandscapes(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    print(" INSTALL OPENSTUDIOLANDSCAPES ".center(_get_terminal_size()[0], "#"))

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

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_etc_hosts() -> pathlib.Path:

    print(" EDIT /etc/hosts ".center(_get_terminal_size()[0], "#"))

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
            ]
        )

        script.writelines(
            [
                "\n",
                "echo \"Your /etc/hosts file looks like:\"\n",
                "cat /etc/hosts\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_harbor_prepare(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    print(" INIT HARBOR ".center(_get_terminal_size()[0], "#"))

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

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_harbor_up(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    print(" INIT HARBOR UP ".center(_get_terminal_size()[0], "#"))

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
                "nox --session harbor_up_detach\n",
                "\n",
                "deactivate\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_harbor_init(
    url_harbor: str = URL_HARBOR,
    username_harbor: str = ADMIN_HARBOR,
    password_harbor: str = PASSWORD_HARBOR,
) -> pathlib.Path:

    print(" INIT HARBOR ".center(_get_terminal_size()[0], "#"))

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
            ]
        )

        # Create `openstudiolandscapes` if it does not exist
        script.writelines(
            [
                "\n",
                "# Create project `openstudiolandscapes`\n",
                "\n",
                "sleep 10\n",
                "\n",
                "curl -X 'POST' \\\n",
                f"  '{url_harbor}/api/v2.0/projects' \\\n",
                "  -H 'accept: application/json' \\\n",
                "  -H 'X-Resource-Name-In-Location: false' \\\n",
                f"  -H 'authorization: Basic {base64.b64encode(str(':'.join([username_harbor, password_harbor])).encode('utf-8')).decode('ascii')}' \\\n",
                "  -H 'Content-Type: application/json' \\\n",
                "  -d '{\n",
                "  \"project_name\": \"openstudiolandscapes\",\n",
                "  \"public\": true\n",
                "}'\n",
                "\n",
                "sleep 10\n",
            ]
        )

        # Delete `library` if it does exist
        script.writelines(
            [
                "\n",
                "# Delete project `library`\n",
                "\n",
                "sleep 10\n",
                "\n",
                "curl -X 'DELETE' \\\n",
                f"  '{url_harbor}/api/v2.0/projects/library' \\\n",
                "  -H 'accept: application/json' \\\n",
                "  -H 'X-Is-Resource-Name: false' \\\n",
                f"  -H 'authorization: Basic {base64.b64encode(str(':'.join([username_harbor, password_harbor])).encode('utf-8')).decode('ascii')}'\n",
                "\n",
                "sleep 10\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_harbor_down(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    print(" INIT HARBOR DOWN ".center(_get_terminal_size()[0], "#"))

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
                "\n",
                "nox --session harbor_down\n",
                "\n",
                "deactivate\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_init_pihole(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
) -> pathlib.Path:

    print(" INIT PI-HOLE ".center(_get_terminal_size()[0], "#"))

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

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_add_alias(
    openstudiolandscapes_repo_dir: pathlib.Path = OPENSTUDIOLANDSCAPES_DIR,
    bashrc: pathlib.Path = pathlib.Path("~/.bashrc").expanduser(),
    openstudiolandscapesrc: pathlib.Path = pathlib.Path("~/.openstudiolandscapesrc").expanduser(),
) -> pathlib.Path:

    print(" ADD ALIASES ".center(_get_terminal_size()[0], "#"))

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
                # Escape dots
                f"sed -i -e '$asource $HOME/\.openstudiolandscapesrc' -e '/source $HOME\/\.openstudiolandscapesrc/d' {bashrc.as_posix()}\n",
            ]
        )

        script.writelines(
            [
                f"cat > {openstudiolandscapesrc.as_posix()}<< EOF\n",
                "# ~/.openstudiolandscapesrc\n",
                f"alias openstudiolandscapes-up=\"pushd {openstudiolandscapes_repo_dir.as_posix()} && source .venv/bin/activate && nox --sessions harbor_up_detach dagster_postgres_up_detach dagster_postgres && deactivate && popd\"\n",
                f"alias openstudiolandscapes-down=\"pushd {openstudiolandscapes_repo_dir.as_posix()} && source .venv/bin/activate && nox --sessions dagster_postgres_down harbor_down && deactivate && popd\"\n",
                "\n",
                "EOF\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


def script_reboot() -> pathlib.Path:

    print(" REBOOT ".center(_get_terminal_size()[0], "#"))

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
                "read -r -e -p \"Reboot now? \" choice_reboot\n",
                "[[ \"$choice_reboot\" == [Yy]* ]] \\\n",
                "    && sudo systemctl reboot \\\n",
                "|| echo \"Ok, let's reboot later.\"\n",
            ]
        )

        script.writelines(
            [
                "\n",
                "exit 0\n",
            ]
        )

        return pathlib.Path(script.name)


if __name__ == "__main__":
    print(" INSTALL DIRECTORY ".center(_get_terminal_size()[0], "#"))
    print(f"Please enter OpenStudiolandscapes install directory:")
    print(f"(Press Enter to continue with the default: {OPENSTUDIOLANDSCAPES_DIR.as_posix()})")
    while True:
        input_ = input()
        if not bool(input_):
            break
        install_dir = pathlib.Path(input_)
        if not install_dir.exists():
            print(f"ERROR: Directory {install_dir.as_posix()} does not exist. Create it first.")
            continue
        if not install_dir.is_dir():
            print(f"ERROR: Install Directory {install_dir.as_posix()} is a file. Cannot continue.")
            continue
        OPENSTUDIOLANDSCAPES_DIR = install_dir
        break

    OPENSTUDIOLANDSCAPES_DIR = pathlib.Path(input() or OPENSTUDIOLANDSCAPES_DIR).expanduser()

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
        sudo=False,
        script=script_install_openstudiolandscapes(),
    )
    ret_script_etc_hosts = script_run(
        sudo=True,
        script=script_etc_hosts(),
    )
    ret_script_harbor_prepare = script_run(
        sudo=False,
        script=script_harbor_prepare(),
    )
    ret_script_harbor_up = script_run(
        sudo=False,
        script=script_harbor_up(),
    )
    ret_script_harbor_init = script_run(
        sudo=False,
        script=script_harbor_init(),
    )
    ret_script_harbor_down = script_run(
        sudo=False,
        script=script_harbor_down(),
    )
    # ret_script_init_pihole = script_run(
    #     sudo=False,
    #     script=script_init_pihole(),
    # )
    ret_script_add_alias = script_run(
        sudo=False,
        script=script_add_alias(),
    )
    ret_script_reboot = script_run(
        sudo=False,
        script=script_reboot(),
    )
