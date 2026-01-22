import argparse
from io import StringIO
import json
import re
import subprocess
import yaml
import jinja2
from importlib.resources import files
import pathlib
import os
import dotenv
import filelock


manifest_filename = "kernel_version_file_list.json"


def semver_key(ver_id):
    # Extract semver part before '+' or '-' or 'rpt' etc.
    match = re.match(r"([0-9]+\.[0-9]+\.[0-9]+)", ver_id)
    if match:
        parts = match.group(1).split(".")
        return tuple(int(p) for p in parts)
    return (0, 0, 0)


def extract_kernel_version_ids_single(apt_list_output: str, target: str) -> list[str]:
    """
    Extracts kernel version IDs from apt list output, filtering by a mandatory target ending.
    Example line:
    linux-headers-6.12.47+rpt-rpi-v8/stable,now 1:6.12.47-1+rpt1 arm64 [installed]
    Returns: ["6.12.25+rpt-rpi-v8", "6.12.34+rpt-rpi-v8", ...] for target="rpi-v8"
    """
    version_ids = []
    pattern = r"linux-headers-([\w\.+-]+" + re.escape(target) + r")(?:/|\s)"
    for line in apt_list_output.strip().splitlines():
        m = re.match(pattern, line)
        if m:
            version_ids.append(m.group(1))
    return sorted(version_ids, key=semver_key, reverse=True)


def extract_kernel_version_ids(
    apt_list_output: str, target: list[str]
) -> dict[str, list[str]]:
    res = {}
    for t in target:
        vers = extract_kernel_version_ids_single(apt_list_output, t)
        res[t] = vers
    return res


def get_args():
    parser = argparse.ArgumentParser(
        description="Cross Driver Configurator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "projectdir",
        type=str,
        help="path to project roo directory containing a'drivercfg.yaml' file",
        default=os.getcwd(),
        nargs="?",
    )
    parser.add_argument(
        "--build",
        help="build the driver using the specified build directory",
        required=False,
    )

    parser.add_argument(
        "--kernel-ver",
        help="kernel version to build the driver against, if not specified all versions will be built",
        required=False,
        nargs="+",
    )

    parser.add_argument(
        "--chroot-root",
        help="path to the kernel modules",
        required=False,
        default="/var/chroot/buildroot/",
    )

    parser.add_argument(
        "--target-dir",
        help="path to the target root filesystem",
        required=False,
        default="/home/crossbuilder/target",
    )

    parser.add_argument(
        "--arch",
        type=str,
        help="target architecture, if not specified the "
        "<target-dir> descriptor will be used to determine",
        required=False,
    )
    parser.add_argument(
        "--kernel-ver-count",
        type=int,
        default=3,
        help="number of last N kernel versions to install",
    )
    parsed = parser.parse_args()
    chrootname = pathlib.Path(parsed.chroot_root).name
    pvars = vars(parsed)
    pvars["chroot_name"] = chrootname
    return argparse.Namespace(**pvars)


def get_arch(targetfile: str) -> str:
    with open(targetfile) as f:
        for line in f.readlines():
            if "TARGET_ARCH=" in line:
                return line.split("=")[1].strip().strip("'")

    raise ValueError("Could not determine target architecture")


def get_template(name: str) -> jinja2.Template:
    template_path = files("xdrvmake").joinpath("templates", f"{name}.j2")
    template_text = template_path.read_text(encoding="utf-8")
    env = jinja2.Environment()

    def tuple_format(value, fmt):
        return fmt.format(*value)

    env.filters["tuple_format"] = tuple_format
    return env.from_string(template_text)


def set_globals(tmpl: jinja2.Template, data: dict) -> jinja2.Template:
    tmpl.globals["project"] = data["project"]
    tmpl.globals["modulename"] = data.get("modulename", None)
    tmpl.globals["sourcedir"] = data.get("sourcedir", "src")
    tmpl.globals["kbuild_flags"] = data.get("kbuild_flags", "")
    tmpl.globals["maintainer"] = data["maintainer"]
    tmpl.globals["description"] = data["description"]
    tmpl.globals["version"] = data["version"]
    tmpl.globals["architecture"] = data["architecture"]
    tmpl.globals["dts_only"] = data.get("dts_only", False)
    tmpl.globals["blacklist"] = data.get("blacklist", None)
    tmpl.globals["public_header"] = data.get("public_header", None)
    tmpl.globals["min_supported"] = data["min_supported"]
    tmpl.globals["max_supported"] = data["max_supported"]
    return tmpl


def create_stating(args: argparse.Namespace, data: dict) -> None:
    os.makedirs("staging/DEBIAN", exist_ok=True)
    files = (
        ("control", "postinst", "postrm", "preinst")
        if not data["dts_only"]
        else ("control", "preinst")
    )
    for file in files:
        render_debian_file(data, file)


def render_debian_file(data, file):
    tmpl = get_template(file)
    set_globals(tmpl, data)
    with open(f"staging/DEBIAN/{file}", "w") as f:
        f.write(tmpl.render())
    if file != "control":
        os.chmod(f"staging/DEBIAN/{file}", 0o755)


def get_kernel_vers(args: argparse.Namespace) -> list[str]:
    if args.kernel_ver is not None:
        return list(args.kernel_ver)

    return [
        entry.name
        for entry in os.scandir(f"{args.chroot_root}/lib/modules")
        if entry.is_dir() and not entry.name.startswith(".")
    ]


def build_driver(args: argparse.Namespace) -> None:
    kernel_vers = get_kernel_vers(args)
    if not kernel_vers:
        raise ValueError("No kernel versions found")
    start_kernels = kernel_vers[0:-1]
    end_kernel = kernel_vers[-1:]
    for kernel_ver in start_kernels:
        exec_make(args, kernel_ver, "driver")
    for kernel_ver in end_kernel:
        exec_make(args, kernel_ver, "all")


def exec_command(cmd: list[str]) -> str:
    popen = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = []
    if popen.stdout is None:
        raise RuntimeError("Failed to capture stdout")
    for line in iter(popen.stdout.readline, b""):
        decoded = line.decode()
        print(decoded, end="")
        lines.append(decoded.strip())
    retcode = popen.wait()
    popen.stdout.close()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)
    return "\n".join(lines)


def exec_make(args: argparse.Namespace, kernel_ver: str, target: str) -> str:
    cmd = ["make", "-C", args.build, target, f"KVER={kernel_ver}"]
    return exec_command(cmd)


def apt_list_kernel_headers_in_buildroot(
    args: argparse.Namespace, globs: list[str]
) -> str:
    return exec_command(
        [
            "schroot",
            "-c",
            args.chroot_name,
            "-u",
            "root",
            "-d",
            "/",
            "--",
            "apt",
            "list",
            "-a",
            *globs,
        ]
    )


def apt_install_kernel_headers_in_buildroot(
    args: argparse.Namespace, packages: list[str]
) -> str:
    return exec_command(
        [
            "schroot",
            "-c",
            args.chroot_name,
            "-u",
            "root",
            "-d",
            "/",
            "--",
            "apt_install",
            "-y",
            "--no-install-recommends",
            *packages,
        ]
    )


def compute_kernel_versions_to_install(
    args: argparse.Namespace,
    available_versions: dict[str, list[str]],
) -> list[str]:
    versions_to_install: list[str] = []
    for plat, vers in available_versions.items():
        versions_to_install.extend(
            (f"linux-headers-{ver}" for ver in vers[: args.kernel_ver_count])
        )
    return versions_to_install


def load_manifest_data(data: dict, versions: dict) -> None:
    min_supported = []
    max_supported = []
    for plat, vers in versions.items():
        vers.sort(key=semver_key)
        min_supported.append((f"linux-image-{plat}", f"1:{vers[0]}"))
        min_supported.append((f"linux-headers-{plat}", f"1:{vers[0]}"))
        max_supported.append((f"linux-image-{plat}", f"1:{vers[-1]}"))
        max_supported.append((f"linux-headers-{plat}", f"1:{vers[-1]}"))
    data["min_supported"] = min_supported
    data["max_supported"] = max_supported


def load_manifest(data: dict) -> None:
    with open(manifest_filename) as f:
        versions: dict = json.load(f)
        load_manifest_data(data, versions)


def compute_and_store_manifest(
    args: argparse.Namespace, versions: dict[str, list[str]]
) -> dict[str, list[str]]:
    version_manifest = {}
    for plat, vers in versions.items():
        vers.sort(key=semver_key, reverse=True)
        version_manifest[plat] = vers[: args.kernel_ver_count]
    with open(manifest_filename, "w") as f:
        json.dump(version_manifest, f, indent=4)
    return version_manifest


def install_kernel_headers(args: argparse.Namespace, data: dict) -> None:
    if os.path.exists(manifest_filename):
        load_manifest(data)
        return

    apt_update_in_buildroot(args)
    plats = get_target_kernel_package_names(open(f"{args.target_dir}/target").read())
    apt_list_pkgs = [f"linux-headers-*-{plat}" for plat in plats]
    apt_list_output = apt_list_kernel_headers_in_buildroot(args, apt_list_pkgs)
    versions = extract_kernel_version_ids(apt_list_output, plats)
    to_install = compute_kernel_versions_to_install(args, versions)
    apt_install_kernel_headers_in_buildroot(args, to_install)
    load_manifest_data(data, compute_and_store_manifest(args, versions))


def apt_update_in_buildroot(args: argparse.Namespace) -> str:
    return exec_command(
        [
            "schroot",
            "-c",
            args.chroot_name,
            "-u",
            "root",
            "-d",
            "/",
            "--",
            "apt_update",
        ]
    )


def main():
    args = get_args()
    if args.build is not None:
        build_driver(args)
        return

    with open(f"{args.projectdir}/drivercfg.yaml") as f:
        data: dict = yaml.safe_load(f)

    if data.get("dts_only", False):
        install_kernel_headers(args, data)

    setup_derived_data(args, data)

    create_makefile(data)

    create_stating(args, data)


def create_makefile(data):
    with open("Makefile", "w") as f:
        f.write(render_makefile(data))


def setup_derived_data(args, data):
    data["projectroot"] = pathlib.Path(args.projectdir).absolute()
    data["architecture"] = args.arch or get_arch(f"{args.target_dir}/target")
    if data["version"] == "auto":
        data["version"] = (
            subprocess.check_output(["git", "describe", "--tags", "--always"])
            .decode()
            .strip()
            .lstrip("v")
        )


def get_target_kernel_package_names(target_file: str) -> list[str]:
    values = dotenv.dotenv_values(stream=StringIO(target_file))
    verlist = (values.get("RPI_KERNEL_VER_LIST") or "").split(",")
    plat_list = [
        m.group(1)
        for ver in verlist
        if (m := re.search(r"-(rpi-.+)$", ver)) is not None
    ]
    if not plat_list:
        raise ValueError("No Raspberry Pi kernel versions found in target file")
    return plat_list


def render_makefile(data: dict) -> str:
    jtmpl = get_template("Makefile")
    jtmpl.globals = data
    set_globals(jtmpl, data)
    res : str = jtmpl.render()
    return res


if __name__ == "__main__":
    lock = filelock.FileLock("xdrvmake.lock")
    with lock:
        main()
