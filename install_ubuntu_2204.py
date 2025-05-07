#!/usr/bin/env python
# https://www.baeldung.com/linux/curl-fetched-script-arguments
import json
import shutil
import subprocess
import tempfile
import pathlib
from getpass import getpass, getuser


# Run this with:
# sudo apt-get install -y curl
# bash <(curl https://raw.githubusercontent.com/michimussato/OpenStudioLandscapes-Temp/refs/heads/main/install_ubuntu_2204.sh)

# This works, but is not very nicely structured
# Maybe split into multiple scripts?
# Write in Python?

# Prep


def sudo_pass() -> bytes:
    _sudo_pass = getpass(prompt='Sudo Password: ')
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


def script_prep_write() -> pathlib.Path:
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
                "sudo apt-get install -y openssh-server git htop vim\n",
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
    # script = script_prep_write()
    ret_script_prep = script_run(
        sudo=True,
        script=script_prep_write(),
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

#
# with tempfile.TemporaryFile("script_2.sh", "w") as script_2:
#     pass


# sudo systemctl enable --now ssh
#
# # Required while not public
# # 1. https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
# read -r -e -p "Type your email: " email
# ssh-keygen -f ~/.ssh/id_ed25519 -N '' -t ed25519 -C "${email}"
# eval "$(ssh-agent -s)"
# ssh-add ~/.ssh/id_ed25519
# # 2. https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account
# # 3. https://github.com/settings/keys
# echo ""
# cat ~/.ssh/id_ed25519.pub
# echo ""
# echo "Copy/Paste above Public Key to GitHub: https://github.com/settings/ssh/new"
#
# while [[ "$choice_ssh" != [Yy]* ]]; do
#     read -r -e -p "Type [Yy]es when ready... " choice_ssh
# done
#
# ssh-keyscan github.com >> ~/.ssh/known_hosts
#
# mkdir -p ~/git/repos/OpenStudioLandscapes
# git -C ~/git/repos clone git@github.com:michimussato/OpenStudioLandscapes.git
# cd ~/git/repos/OpenStudioLandscapes || exit
#
#
# # Install OpenStudioLandscapes
#
# # https://itsfoss.com/could-not-get-lock-error/
# # stat /var/lib/dpkg/lock
# # stat /var/lib/dpkg/lock-frontend
# # ps aux | grep -i apt
#
# if ! sudo apt-get upgrade -y; then
#     echo "Update in progress in the background."
#     echo "Let the process finish and run this script afterwards."
#     exit 1
# fi;
#
# # Install Python 3.11
# export PYTHON_MAJ="3"
# export PYTHON_MIN="11"
# export PYTHON_PAT="11"
#
# sudo apt-get install -y \
#     build-essential \
#     zlib1g-dev \
#     libncurses5-dev \
#     libgdbm-dev \
#     libnss3-dev \
#     libssl-dev \
#     libreadline-dev \
#     libffi-dev \
#     wget \
#     pkg-config \
#     liblzma-dev \
#     libbz2-dev \
#     libsqlite3-dev \
#     curl
#
# pushd "$(mktemp -d)" || exit
#
# curl "https://www.python.org/ftp/python/${PYTHON_MAJ}.${PYTHON_MIN}.${PYTHON_PAT}/Python-${PYTHON_MAJ}.${PYTHON_MIN}.${PYTHON_PAT}.tgz" -o Python-${PYTHON_MAJ}.${PYTHON_MIN}.${PYTHON_PAT}.tgz
# tar -xvf Python-${PYTHON_MAJ}.${PYTHON_MIN}.${PYTHON_PAT}.tgz
# cd Python-${PYTHON_MAJ}.${PYTHON_MIN}.${PYTHON_PAT} || exit
#
# ./configure --enable-optimizations
# make -j "$(nproc)"
# sudo make altinstall
#
# popd || exit
#
# # Install Docker
# # # https://docs.docker.com/engine/install/ubuntu/
# for pkg in \
#     docker.io \
#     docker-doc \
#     docker-compose \
#     docker-compose-v2 \
#     podman-docker \
#     containerd \
#     runc\
#     ; do sudo apt-get remove $pkg; done
# sudo apt autoremove -y
#
# sudo apt-get update
# sudo apt-get install ca-certificates curl
# sudo install -m 0755 -d /etc/apt/keyrings
# sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# sudo chmod a+r /etc/apt/keyrings/docker.asc
#
# # Add trust for insecure harbor.farm.evil
# #read -e -p "Do you want me to configure /etc/docker/daemon.json?" choice
# #[[ "$choice" == [Yy]* ]] \
# #    && sudo -s << EOF
# #mkdir -p /etc/docker
# #touch /etc/docker/daemon.json
# #cat > /etc/docker/daemon.json
# #{
# #  "insecure-registries" : [
# #    "http://harbor.farm.evil:80"
# #  ],
# #  "max-concurrent-uploads": 1
# #}
# #EOF
# #|| echo "Ok, I didn't."
# sudo -s << EOF
# mkdir -p /etc/docker
# touch /etc/docker/daemon.json
# cat > /etc/docker/daemon.json
# {
#   "insecure-registries" : [
#     "http://harbor.farm.evil:80"
#   ],
#   "max-concurrent-uploads": 1
# }
# EOF
#
# echo \
#   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
#   $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
#   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
# sudo apt-get update
#
# sudo apt-get install -y \
#     docker-ce \
#     docker-ce-cli \
#     containerd.io \
#     docker-buildx-plugin \
#     docker-compose-plugin
#
# # # https://docs.docker.com/engine/install/linux-postinstall/
# sudo groupadd --force docker
# sudo usermod --append --groups docker "${USER}"
#
# # This is to prevent the need to logout/login
# # exec su -l "${USER}"
#
# sudo systemctl daemon-reload
# sudo systemctl restart docker
#
# # Install OpenStudioLandscapes
# sudo apt-get install -y graphviz
# python3.11 -m venv .venv
# source .venv/bin/activate
# pip install --upgrade pip setuptools setuptools_scm wheel
# pip install -e .[dev]
#
# nox -s clone_features
# nox -s install_features_into_engine
#
# deactivate
#
# read -r -e -p "Do you want me to add entries to /etc/hosts? " choice_hosts
# [[ "$choice_hosts" == [Yy]* ]] \
#     && sudo sed -i -e '$a127.0.0.1    dagster.farm.evil' -e '/127.0.0.1    dagster.farm.evil/d' /etc/hosts \
#     && sudo sed -i -e '$a127.0.0.1    postgres-dagster.farm.evil' -e '/127.0.0.1    postgres-dagster.farm.evil/d' /etc/hosts \
#     && sudo sed -i -e '$a127.0.0.1    harbor.farm.evil' -e '/127.0.0.1    harbor.farm.evil/d' /etc/hosts \
#     && sudo sed -i -e '$a127.0.0.1    pi-hole.farm.evil' -e '/127.0.0.1    harbor.farm.evil/d' /etc/hosts \
# || echo "Ok, I didn't."
#
# echo ""
# echo "Your /etc/hosts file looks like:"
# sudo cat /etc/hosts
# echo ""
#
# echo ""
# echo "Your /etc/docker/daemon.json file looks like:"
# sudo cat /etc/docker/daemon.json
# echo ""
#
# read -r -e -p "Initialize Harbor? " choice_harbor
# # Todo
# #  - [ ] password required when sudo as USER?
# [[ "$choice_harbor" == [Yy]* ]] \
#     && read -r -s -p "Password for sudo user ${USER}: " password \
#     && echo "${password}" | sudo -S -u ${USER} -- bash -c "cd ~/git/repos/OpenStudioLandscapes && source .venv/bin/activate && nox --session harbor_prepare && deactivate" \
# || echo "Ok, you'll do it yourself."
#
# read -r -e -p "Initialize Pi-Hole? " choice_pihole
# [[ "$choice_pihole" == [Yy]* ]] \
#     && cd ~/git/repos/OpenStudioLandscapes \
#     && source .venv/bin/activate \
#     && nox --session pi_hole_prepare \
#     && deactivate \
# || echo "Ok, you'll do it yourself."
#
# echo "Reboot system please."
# echo "Remember to create project 'openstudiolandscapes' in Harbor afterwards."
#
# read -r -e -p "Reboot now? " choice_reboot
# [[ "$choice_reboot" == [Yy]* ]] \
#     && sudo systemctl reboot \
# || echo "Ok, let's reboot later."
#
# exit 0
