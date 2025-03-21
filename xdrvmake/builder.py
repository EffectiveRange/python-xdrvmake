import argparse
import subprocess
import yaml
import jinja2
import pkg_resources
import pathlib
import os


def get_args():
    parser = argparse.ArgumentParser(
        description="Cross Driver Configurator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "projectdir",
        type=str,
        help="path to project roo directory containing a'drivercfg.yaml' file",
    )
    parser.add_argument("--build", action="store_true", help="build the driver")
    return parser.parse_args()


def get_arch(targetfile: str):
    with open(targetfile) as f:
        for line in f.readlines():
            if "TARGET_ARCH=" in line:
                return line.split("=")[1].strip().strip("'")

    raise ValueError("Could not determine target architecture")


def get_template(name: str) -> jinja2.Template:
    config_path = pkg_resources.resource_filename("xdrvmake", f"templates/{name}.j2")
    with open(config_path, "r") as f:
        content = f.read()
    return jinja2.Template(content)


def set_globals(tmpl: jinja2.Template, data: dict):
    tmpl.globals["project"] = data["project"]
    tmpl.globals["modulename"] = data["modulename"]
    tmpl.globals["sourcedir"] = data.get("sourcedir", "src")
    tmpl.globals["kbuild_flags"] = data.get("kbuild_flags", "")
    tmpl.globals["maintainer"] = data["maintainer"]
    tmpl.globals["description"] = data["description"]
    tmpl.globals["version"] = data["version"]
    tmpl.globals["architecture"] = data["architecture"]
    return tmpl


def create_stating(args: argparse.Namespace, data: dict):
    os.makedirs(f"staging/DEBIAN", exist_ok=True)
    for file in ("control", "postinst", "postrm", "preinst"):
        tmpl = get_template(file)
        set_globals(tmpl, data)
        with open(f"staging/DEBIAN/{file}", "w") as f:
            f.write(tmpl.render())
        if file != "control":
            os.chmod(f"staging/DEBIAN/{file}", 0o755)


def main():
    args = get_args()

    with open(f"{args.projectdir}/drivercfg.yaml") as f:
        data: dict = yaml.safe_load(f)
    setup_derived_data(args, data)

    create_makefile(data)

    create_stating(args, data)


def create_makefile(data):
    with open(f"Makefile", "w") as f:
        f.write(render_makefile(data))


def setup_derived_data(args, data):
    data["projectroot"] = pathlib.Path(args.projectdir).absolute()
    data["architecture"] = get_arch(f"/home/crossbuilder/target/target")
    if data["version"] == "auto":
        data["version"] = (
            subprocess.check_output(["git", "describe", "--tags", "--always"])
            .decode()
            .strip()
            .lstrip("v")
        )


def render_makefile(data: dict) -> str:
    jtmpl = get_template("Makefile")
    jtmpl.globals = data
    set_globals(jtmpl, data)
    return jtmpl.render()


if __name__ == "__main__":
    main()
