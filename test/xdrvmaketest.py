#!/usr/bin/python3 -u

import argparse
import unittest
import textwrap
from xdrvmake.builder import (
    compute_kernel_versions_to_install,
    extract_kernel_version_ids_single,
    get_target_kernel_package_names,
    extract_kernel_version_ids,
)

sample_target_file = textwrap.dedent(
    """\
    RPI_KERNEL_VER_LIST='linux-headers-6.12.47+rpt-rpi-2712,linux-headers-6.12.47+rpt-rpi-v8,'
    """
)

sample_target_file_armhf = textwrap.dedent(
    """\
    RPI_KERNEL_VER_LIST='linux-headers-6.12.47+rpt-rpi-v6,linux-headers-6.12.47+rpt-rpi-v7,'
    """
)


apt_list_output = textwrap.dedent(
    """\
linux-headers-6.12.25+rpt-rpi-v8/stable 1:6.12.25-1+rpt1+trixie arm64

linux-headers-6.12.34+rpt-rpi-v8/stable 1:6.12.34-1+rpt1 arm64

linux-headers-6.12.47+rpt-rpi-v8/stable,now 1:6.12.47-1+rpt1 arm64 [installed]

linux-headers-6.12.62+rpt-rpi-v8/stable,now 1:6.12.62-1+rpt1 arm64 [installed]
"""
)


apt_list_out_2712 = textwrap.dedent(
    """\
linux-headers-6.12.34+rpt-rpi-2712/stable 1:6.12.34-1+rpt1 arm64

linux-headers-6.12.47+rpt-rpi-2712/stable,now 1:6.12.47-1+rpt1 arm64 [installed]

linux-headers-6.12.62+rpt-rpi-2712/stable,now 1:6.12.62-1+rpt1 arm64 [installed]
"""
)

apt_list_combined = textwrap.dedent(
    """\
linux-headers-6.12.25+rpt-rpi-2712/stable 1:6.12.25-1+rpt1+trixie arm64

linux-headers-6.12.25+rpt-rpi-v8/stable 1:6.12.25-1+rpt1+trixie arm64

linux-headers-6.12.34+rpt-rpi-2712/stable 1:6.12.34-1+rpt1 arm64

linux-headers-6.12.34+rpt-rpi-v8/stable 1:6.12.34-1+rpt1 arm64

linux-headers-6.12.47+rpt-rpi-2712/stable,now 1:6.12.47-1+rpt1 arm64 [installed]

linux-headers-6.12.47+rpt-rpi-v8/stable,now 1:6.12.47-1+rpt1 arm64 [installed]

linux-headers-6.12.62+rpt-rpi-2712/stable,now 1:6.12.62-1+rpt1 arm64 [installed]

linux-headers-6.12.62+rpt-rpi-v8/stable,now 1:6.12.62-1+rpt1 arm64 [installed]

"""
)


class TestAptKernelVersionParsing(unittest.TestCase):
    def test_kernel_ver_count_zero(self):
        available_versions = {
            "rpi-2712": [
                "6.12.62+rpt-rpi-2712",
                "6.12.47+rpt-rpi-2712",
                "6.12.34+rpt-rpi-2712",
                "6.12.25+rpt-rpi-2712",
            ],
            "rpi-v8": [
                "6.12.62+rpt-rpi-v8",
                "6.12.47+rpt-rpi-v8",
                "6.12.34+rpt-rpi-v8",
                "6.12.25+rpt-rpi-v8",
            ],
        }
        computed = compute_kernel_versions_to_install(
            argparse.Namespace(kernel_ver_count=0), available_versions
        )
        self.assertEqual(computed, [])

    def test_finding_rpi_plats(self):
        plats = get_target_kernel_package_names(sample_target_file)
        self.assertEqual(
            plats,
            ["rpi-2712", "rpi-v8"],
        )

    def test_finding_rpi_plats_armhf(self):
        plats = get_target_kernel_package_names(sample_target_file_armhf)
        self.assertEqual(
            plats,
            ["rpi-v6", "rpi-v7"],
        )

    def test_parsing_apt_output_rpi_v8(self):
        versions = extract_kernel_version_ids_single(apt_list_output, "rpi-v8")
        self.assertEqual(
            versions,
            [
                "6.12.62+rpt-rpi-v8",
                "6.12.47+rpt-rpi-v8",
                "6.12.34+rpt-rpi-v8",
                "6.12.25+rpt-rpi-v8",
            ],
        )

    def test_parsing_apt_output_rpi_2712(self):
        versions = extract_kernel_version_ids_single(apt_list_out_2712, "rpi-2712")
        self.assertEqual(
            versions,
            [
                "6.12.62+rpt-rpi-2712",
                "6.12.47+rpt-rpi-2712",
                "6.12.34+rpt-rpi-2712",
            ],
        )

    def test_parsing_apt_output_combined(self):
        versions = extract_kernel_version_ids(apt_list_combined, ["rpi-2712", "rpi-v8"])
        self.assertDictEqual(
            versions,
            {
                "rpi-2712": [
                    "6.12.62+rpt-rpi-2712",
                    "6.12.47+rpt-rpi-2712",
                    "6.12.34+rpt-rpi-2712",
                    "6.12.25+rpt-rpi-2712",
                ],
                "rpi-v8": [
                    "6.12.62+rpt-rpi-v8",
                    "6.12.47+rpt-rpi-v8",
                    "6.12.34+rpt-rpi-v8",
                    "6.12.25+rpt-rpi-v8",
                ],
            },
        )

    def test_compute_kernel_versions_to_install(self):
        available_versions = {
            "rpi-2712": [
                "6.12.62+rpt-rpi-2712",
                "6.12.47+rpt-rpi-2712",
                "6.12.34+rpt-rpi-2712",
                "6.12.25+rpt-rpi-2712",
            ],
            "rpi-v8": [
                "6.12.62+rpt-rpi-v8",
                "6.12.47+rpt-rpi-v8",
                "6.12.34+rpt-rpi-v8",
                "6.12.25+rpt-rpi-v8",
            ],
        }
        to_install = [
            "linux-headers-6.12.62+rpt-rpi-2712",
            "linux-headers-6.12.47+rpt-rpi-2712",
            "linux-headers-6.12.34+rpt-rpi-2712",
            "linux-headers-6.12.62+rpt-rpi-v8",
            "linux-headers-6.12.47+rpt-rpi-v8",
            "linux-headers-6.12.34+rpt-rpi-v8",
        ]

        computed = compute_kernel_versions_to_install(
            argparse.Namespace(kernel_ver_count=3), available_versions
        )
        self.assertEqual(computed, to_install)


class TestBuilderUtils(unittest.TestCase):

    def test_semver_key(self):
        from xdrvmake.builder import semver_key

        self.assertEqual(semver_key("6.12.34+rpt-rpi-v8"), (6, 12, 34))
        self.assertEqual(semver_key("1.2.3"), (1, 2, 3))
        self.assertEqual(semver_key("foo"), (0, 0, 0))

    def test_get_arch(self):
        import tempfile
        from xdrvmake.builder import get_arch

        with tempfile.NamedTemporaryFile("w+t", delete=True) as f:
            f.write("TARGET_ARCH='arm64'\n")
            f.seek(0)
            self.assertEqual(get_arch(f.name), "arm64")
        with tempfile.NamedTemporaryFile("w+t", delete=True) as f:
            f.write("SOMETHING_ELSE=1\n")
            f.seek(0)
            with self.assertRaises(ValueError):
                get_arch(f.name)

    def test_get_template_and_render(self):
        from xdrvmake.builder import get_template

        # Just check that it loads a template and renders without error
        tmpl = get_template("Makefile")
        self.assertTrue(hasattr(tmpl, "render"))

    def test_set_globals(self):
        from xdrvmake.builder import get_template, set_globals

        tmpl = get_template("Makefile")
        data = {
            "project": "foo",
            "maintainer": "bar",
            "description": "desc",
            "version": "1.0",
            "architecture": "arm64",
            "min_supported": [],
            "max_supported": [],
        }
        tmpl = set_globals(tmpl, data)
        self.assertEqual(tmpl.globals["project"], "foo")
        self.assertEqual(tmpl.globals["maintainer"], "bar")

    def test_load_manifest_data(self):
        from xdrvmake.builder import load_manifest_data

        data: dict = {}
        versions = {"plat": ["6.12.34+rpt-plat", "6.12.62+rpt-plat"]}
        load_manifest_data(data, versions)
        self.assertIn("min_supported", data)
        self.assertIn("max_supported", data)
        self.assertTrue(any("linux-image-plat" in x for x, _ in data["min_supported"]))

    def test_compute_and_store_manifest(self):
        import tempfile
        import os
        import json
        from xdrvmake.builder import compute_and_store_manifest

        versions = {"plat": ["6.12.62+rpt-rpi-plat", "6.12.34+rpt-rpi-plat"]}
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                _ = compute_and_store_manifest(
                    argparse.Namespace(kernel_ver_count=1), versions
                )
                self.assertTrue(os.path.exists("kernel_version_file_list.json"))
                with open("kernel_version_file_list.json") as f:
                    data = json.load(f)
                self.assertEqual(data["plat"], ["6.12.62+rpt-rpi-plat"])
            finally:
                os.chdir(old)

    def test_exec_command(self):
        from xdrvmake.builder import exec_command

        # Test a simple echo command
        output = exec_command(["echo", "hello world"])
        self.assertIn("hello world", output)

        # Test a command that fails
        with self.assertRaises(Exception):
            exec_command(["false"])

    def test_render_debian_file_and_create_stating(self):
        import tempfile
        import os
        from xdrvmake.builder import render_debian_file, create_stating

        # Minimal data for template rendering
        data: dict = {
            "project": "testproj",
            "maintainer": "maint",
            "description": "desc",
            "version": "1.0",
            "architecture": "arm64",
            "min_supported": [
                ("linux-image-testproj", "1:6.12.34+rpt-testproj"),
                ("linux-headers-testproj", "1:6.12.34+rpt-testproj"),
            ],
            "max_supported": [
                ("linux-image-testproj", "1:6.12.62+rpt-testproj"),
                ("linux-headers-testproj", "1:6.12.62+rpt-testproj"),
            ],
            "dts_only": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                os.makedirs("staging/DEBIAN", exist_ok=True)  # Ensure directory exists
                render_debian_file(data, "control")
                self.assertTrue(os.path.exists("staging/DEBIAN/control"))
                with open("staging/DEBIAN/control") as f:
                    control_content = f.read()
                print("\n--- Rendered control file ---\n", control_content)
                self.assertIn("Package: testproj", control_content)
                self.assertIn("Version: 1.0", control_content)
                self.assertIn("Maintainer: maint", control_content)
                self.assertIn(
                    "linux-image-testproj (>>1:6.12.62+rpt-testproj)", control_content
                )
                self.assertIn(
                    "linux-headers-testproj (>>1:6.12.62+rpt-testproj)", control_content
                )
                self.assertIn(
                    "linux-image-testproj (>=1:6.12.34+rpt-testproj)", control_content
                )
                self.assertIn(
                    "linux-headers-testproj (>=1:6.12.34+rpt-testproj)", control_content
                )
                # Test create_stating (should create all files)
                create_stating(type("Args", (), {})(), data)
                for fname in ["control", "postinst", "postrm", "triggers"]:
                    self.assertTrue(os.path.exists(f"staging/DEBIAN/{fname}"))
            finally:
                os.chdir(cwd)

    def test_get_args_parsing(self):
        import sys
        from xdrvmake.builder import get_args

        old_argv = sys.argv
        try:
            sys.argv = [
                "prog",
                "/tmp/project",
                "--build",
                "/tmp/build",
                "--kernel-ver",
                "foo",
                "bar",
                "--arch",
                "armhf",
                "--kernel-ver-count",
                "2",
            ]
            args = get_args()
            self.assertEqual(args.projectdir, "/tmp/project")
            self.assertEqual(args.build, "/tmp/build")
            self.assertEqual(args.kernel_ver, ["foo", "bar"])
            self.assertEqual(args.arch, "armhf")
            self.assertEqual(args.kernel_ver_count, 2)
            self.assertEqual(args.chroot_name, "buildroot")
        finally:
            sys.argv = old_argv

    def test_get_kernel_vers(self):
        import tempfile
        import os
        from xdrvmake.builder import get_kernel_vers

        Args = argparse.Namespace(kernel_ver=None, chroot_root=None)

        with tempfile.TemporaryDirectory() as tmp:
            lib_modules = os.path.join(tmp, "lib", "modules")
            os.makedirs(lib_modules)
            os.makedirs(os.path.join(lib_modules, "6.12.34"))
            os.makedirs(os.path.join(lib_modules, "6.12.47"))
            Args.chroot_root = tmp
            vers = get_kernel_vers(Args)
            self.assertIn("6.12.34", vers)
            self.assertIn("6.12.47", vers)
            self.assertEqual(sorted(vers), ["6.12.34", "6.12.47"])
        Args.kernel_ver = ["foo", "bar"]
        self.assertEqual(get_kernel_vers(Args), ["foo", "bar"])

    def test_build_driver(self):
        from xdrvmake.builder import build_driver

        called = []

        def fake_exec_make(args, target):
            called.append(target)

        # Patch exec_make
        import xdrvmake.builder

        old_exec_make = xdrvmake.builder.exec_make
        xdrvmake.builder.exec_make = fake_exec_make

        try:
            build_driver(argparse.Namespace(build="/test"))
            # Should call make all target (Makefile handles per-version builds)
            self.assertEqual(called, ["all"])
        finally:
            xdrvmake.builder.exec_make = old_exec_make

    def test_parallel_build_args_parsing(self):
        import sys
        import os
        from xdrvmake.builder import get_args

        old_argv = sys.argv
        try:
            # Test with -j flag
            sys.argv = ["prog", "/tmp/project", "-j", "4"]
            args = get_args()
            self.assertEqual(args.jobs, 4)

            # Test with --jobs flag
            sys.argv = ["prog", "/tmp/project", "--jobs", "8"]
            args = get_args()
            self.assertEqual(args.jobs, 8)

            # Test default (no -j flag) - should be number of CPUs
            sys.argv = ["prog", "/tmp/project"]
            args = get_args()
            self.assertEqual(args.jobs, os.cpu_count() or 1)
        finally:
            sys.argv = old_argv

    def test_exec_make_with_parallel_jobs(self):
        from xdrvmake.builder import exec_make
        import xdrvmake.builder

        called_cmds = []

        def fake_exec_command(cmd):
            called_cmds.append(cmd)
            return ""

        old_exec_command = xdrvmake.builder.exec_command
        xdrvmake.builder.exec_command = fake_exec_command

        try:
            # Test with jobs=1 (no -j flag)
            args = argparse.Namespace(build="/test/build", jobs=1)
            exec_make(args, "all")
            self.assertEqual(called_cmds[-1], ["make", "-C", "/test/build", "all"])

            # Test with jobs=4 (should add -j 4)
            args = argparse.Namespace(build="/test/build", jobs=4)
            exec_make(args, "all")
            self.assertEqual(
                called_cmds[-1], ["make", "-C", "/test/build", "-j", "4", "all"]
            )

            # Test with jobs=8
            args = argparse.Namespace(build="/test/build", jobs=8)
            exec_make(args, "driver")
            self.assertEqual(
                called_cmds[-1], ["make", "-C", "/test/build", "-j", "8", "driver"]
            )
        finally:
            xdrvmake.builder.exec_command = old_exec_command

    def test_install_kernel_headers_and_load_manifest(self):
        import tempfile
        import shutil
        import os
        import json
        from unittest.mock import patch

        # Setup temp dirs and files
        temp_dir = tempfile.mkdtemp()
        chroot_root = os.path.join(temp_dir, "chroot")
        target_dir = os.path.join(temp_dir, "target")
        os.makedirs(f"{chroot_root}/lib/modules/6.1.0-test", exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        with open(f"{target_dir}/target", "w") as f:
            f.write(
                "RPI_KERNEL_VER_LIST=6.1.0-rpi-v8,6.1.0-rpi-v7\nTARGET_ARCH='arm64'\n"
            )

        # Prepare args
        args = argparse.Namespace(
            chroot_root=chroot_root,
            target_dir=target_dir,
            chroot_name="buildroot",
            kernel_ver_count=1,
        )
        data = {
            "project": "TestProj",
            "modulename": "testmod",
            "sourcedir": "src",
            "kbuild_flags": "",
            "maintainer": "Test Maintainer",
            "description": "Test Desc",
            "version": "1.0.0",
            "architecture": "arm64",
            "dts_only": False,
            "blacklist": None,
            "public_header": None,
            "min_supported": [],
            "max_supported": [],
        }
        manifest_path = os.path.join(os.getcwd(), "kernel_version_file_list.json")
        if os.path.exists(manifest_path):
            os.remove(manifest_path)

        with patch(
            "xdrvmake.builder.exec_command",
            return_value="linux-headers-6.1.0-rpi-v8/stable,now 1:6.1.0-1+rpt1 arm64 [installed]\n"
            "linux-headers-6.1.0-rpi-v7/stable,now 1:6.1.0-1+rpt1 arm64 [installed]",
        ), patch("xdrvmake.builder.apt_update_in_buildroot", return_value=None), patch(
            "xdrvmake.builder.apt_install_kernel_headers_in_buildroot",
            return_value=None,
        ):
            from xdrvmake import builder

            builder.install_kernel_headers(args, data)
            self.assertTrue(os.path.exists(manifest_path))
            with open(manifest_path) as f:
                manifest = json.load(f)
            self.assertIn("rpi-v8", manifest)
            self.assertIn("rpi-v7", manifest)
            self.assertTrue(data["min_supported"])
            self.assertTrue(data["max_supported"])
            # Test load_manifest (should update data from manifest)
            data2 = data.copy()
            data2["min_supported"] = []
            data2["max_supported"] = []
            builder.load_manifest(data2)
            self.assertTrue(data2["min_supported"])
            self.assertTrue(data2["max_supported"])
        shutil.rmtree(temp_dir)
        if os.path.exists(manifest_path):
            os.remove(manifest_path)

    def test_setup_derived_data(self):
        import tempfile
        import os
        from xdrvmake.builder import setup_derived_data

        # Create a dummy target file
        with tempfile.TemporaryDirectory() as tmp:
            target_file = os.path.join(tmp, "target")
            with open(target_file, "w") as f:
                f.write("TARGET_ARCH='arm64'\n")
            args = type(
                "Args",
                (),
                {
                    "projectdir": tmp,
                    "arch": None,
                    "target_dir": tmp,
                    "version": "1.0.0",
                },
            )()
            data = {"version": "1.0.0"}
            setup_derived_data(args, data)
            self.assertEqual(data["architecture"], "arm64")
            self.assertEqual(str(data["projectroot"]), str(os.path.abspath(tmp)))
            # Test auto version
            data2 = {"version": "auto"}
            with tempfile.TemporaryDirectory() as gitdir:
                old = os.getcwd()
                os.chdir(gitdir)
                try:
                    os.system(
                        'git init && git config user.email "you@example.com" && git config user.name "Your Name"  &&'
                        ' git commit --allow-empty -m "init" && git tag v1.2.3'
                    )
                    args2 = type(
                        "Args",
                        (),
                        {"projectdir": gitdir, "arch": None, "target_dir": tmp},
                    )()
                    setup_derived_data(args2, data2)
                    self.assertTrue(data2["version"].startswith("1.2.3"))
                finally:
                    os.chdir(old)

    def test_create_makefile(self):
        import tempfile
        import os
        from xdrvmake.builder import create_makefile

        data = {
            "project": "testproj",
            "maintainer": "maint",
            "description": "desc",
            "version": "1.0",
            "architecture": "arm64",
            "min_supported": [
                ("linux-image-testproj", "1:6.12.34+rpt-testproj"),
                ("linux-headers-testproj", "1:6.12.34+rpt-testproj"),
            ],
            "max_supported": [
                ("linux-image-testproj", "1:6.12.62+rpt-testproj"),
                ("linux-headers-testproj", "1:6.12.62+rpt-testproj"),
            ],
            "kernel_versions": [
                "6.12.34+rpt-testproj",
                "6.12.62+rpt-testproj",
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                create_makefile(data)
                self.assertTrue(os.path.exists("Makefile"))
                with open("Makefile") as f:
                    content = f.read()
                self.assertIn("testproj", content)
                self.assertIn("arm64", content)
            finally:
                os.chdir(old)

    def test_makefile_full_driver_with_version_targets(self):
        from xdrvmake.builder import render_makefile

        data = {
            "project": "mydriver",
            "modulename": "mymod",
            "sourcedir": "src",
            "kbuild_flags": "",
            "maintainer": "test@example.com",
            "description": "Test driver",
            "version": "1.0.0",
            "architecture": "arm64",
            "dts_only": False,
            "blacklist": None,
            "public_header": None,
            "min_supported": [("linux-image-rpi-v8", "1:6.12.34+rpt-rpi-v8")],
            "max_supported": [("linux-image-rpi-v8", "1:6.12.62+rpt-rpi-v8")],
            "kernel_versions": [
                "6.12.34+rpt-rpi-v8",
                "6.12.62+rpt-rpi-v8",
                "6.6.73+rpt-rpi-v8",
            ],
            "projectroot": "/test/project",
        }

        makefile = render_makefile(data)

        # Verify version-specific driver targets exist
        self.assertIn("driver-6.12.34+rpt-rpi-v8:", makefile)
        self.assertIn("driver-6.12.62+rpt-rpi-v8:", makefile)
        self.assertIn("driver-6.6.73+rpt-rpi-v8:", makefile)

        # Verify version-specific quickdeploy targets exist (not dts_only)
        self.assertIn("quickdeploy-6.12.34+rpt-rpi-v8:", makefile)
        self.assertIn("quickdeploy-6.12.62+rpt-rpi-v8:", makefile)
        self.assertIn("quickdeploy-6.6.73+rpt-rpi-v8:", makefile)

        # Verify quickdeploy has correct dependencies and commands
        self.assertIn(
            "quickdeploy-6.12.34+rpt-rpi-v8: driver-6.12.34+rpt-rpi-v8", makefile
        )
        self.assertIn("scp staging/lib/modules/6.12.34+rpt-rpi-v8/mymod.ko", makefile)
        self.assertIn("sudo rmmod mymod", makefile)
        self.assertIn("sudo modprobe mymod", makefile)

        # Verify aggregate all-drivers target
        self.assertIn("all-drivers:", makefile)
        self.assertIn("driver-6.12.34+rpt-rpi-v8", makefile)
        self.assertIn("driver-6.12.62+rpt-rpi-v8", makefile)
        self.assertIn("driver-6.6.73+rpt-rpi-v8", makefile)

        # Verify .ko file targets
        self.assertIn("staging/lib/modules/6.12.34+rpt-rpi-v8/mymod.ko:", makefile)
        self.assertIn("staging/lib/modules/6.12.62+rpt-rpi-v8/mymod.ko:", makefile)
        self.assertIn("staging/lib/modules/6.6.73+rpt-rpi-v8/mymod.ko:", makefile)

        # Verify unique temp build directories per kernel version (prevents race conditions)
        self.assertIn("/tmp/drv-mydriver-6.12.34+rpt-rpi-v8", makefile)
        self.assertIn("/tmp/drv-mydriver-6.12.62+rpt-rpi-v8", makefile)
        self.assertIn("/tmp/drv-mydriver-6.6.73+rpt-rpi-v8", makefile)
        # Ensure no shared temp directory
        self.assertNotIn(
            "rsync --delete -r  /test/project/src/ /tmp/drv-mydriver\n", makefile
        )
        self.assertNotIn(
            "schroot -c buildroot -u root -d /tmp/drv-mydriver --", makefile
        )

        # Verify DTBO targets
        self.assertIn(
            "staging/usr/lib/er-overlays/6.12.34+rpt-rpi-v8/mydriver.dtbo:", makefile
        )
        self.assertIn(
            "staging/usr/lib/er-overlays/6.12.62+rpt-rpi-v8/mydriver.dtbo:", makefile
        )

        # Verify .PHONY contains all targets
        self.assertIn(".PHONY:", makefile)
        # Check that PHONY line has the driver targets
        phony_lines = [
            line for line in makefile.split("\n") if line.startswith(".PHONY:")
        ]
        self.assertTrue(len(phony_lines) > 0)
        phony_content = " ".join(phony_lines)
        self.assertIn("driver-6.12.34+rpt-rpi-v8", phony_content)
        self.assertIn("quickdeploy-6.12.34+rpt-rpi-v8", phony_content)
        self.assertIn("all-drivers", phony_content)

        # Verify no generic KVER variable targets
        self.assertNotIn("KVER ?=", makefile)
        self.assertNotIn("driver: staging/lib/modules/$(KVER)", makefile)

        # Verify kernel version list comment
        self.assertIn(
            "KERNEL_VERSIONS = 6.12.34+rpt-rpi-v8 6.12.62+rpt-rpi-v8 6.6.73+rpt-rpi-v8",
            makefile,
        )

    def test_makefile_dts_only_no_quickdeploy(self):
        from xdrvmake.builder import render_makefile

        data = {
            "project": "myoverlay",
            "modulename": None,  # No module for dts_only
            "sourcedir": "src",
            "kbuild_flags": "",
            "maintainer": "test@example.com",
            "description": "Test overlay",
            "version": "1.0.0",
            "architecture": "arm64",
            "dts_only": True,  # DTS only mode
            "blacklist": None,
            "public_header": None,
            "min_supported": [("linux-image-rpi-v8", "1:6.12.34+rpt-rpi-v8")],
            "max_supported": [("linux-image-rpi-v8", "1:6.12.62+rpt-rpi-v8")],
            "kernel_versions": [
                "6.12.34+rpt-rpi-v8",
                "6.12.62+rpt-rpi-v8",
            ],
            "projectroot": "/test/project",
        }

        makefile = render_makefile(data)

        # Verify version-specific driver targets exist
        self.assertIn("driver-6.12.34+rpt-rpi-v8:", makefile)
        self.assertIn("driver-6.12.62+rpt-rpi-v8:", makefile)

        # Verify NO quickdeploy targets (dts_only mode)
        self.assertNotIn("quickdeploy-6.12.34+rpt-rpi-v8:", makefile)
        self.assertNotIn("quickdeploy-6.12.62+rpt-rpi-v8:", makefile)
        self.assertNotIn("rmmod", makefile)
        self.assertNotIn("modprobe", makefile)

        # Verify NO .ko file targets (dts_only)
        self.assertNotIn("staging/lib/modules/", makefile)
        self.assertNotIn(".ko:", makefile)

        # Verify DTBO targets still exist
        self.assertIn(
            "staging/usr/lib/er-overlays/6.12.34+rpt-rpi-v8/myoverlay.dtbo:", makefile
        )
        self.assertIn(
            "staging/usr/lib/er-overlays/6.12.62+rpt-rpi-v8/myoverlay.dtbo:", makefile
        )

        # Verify driver targets depend only on DTBO (not .ko)
        self.assertIn(
            "driver-6.12.34+rpt-rpi-v8: staging/usr/lib/er-overlays/6.12.34+rpt-rpi-v8/myoverlay.dtbo",
            makefile,
        )

        # Verify aggregate all-drivers target
        self.assertIn("all-drivers:", makefile)
        self.assertIn("driver-6.12.34+rpt-rpi-v8", makefile)
        self.assertIn("driver-6.12.62+rpt-rpi-v8", makefile)

        # Verify .PHONY does NOT contain quickdeploy targets
        phony_lines = [
            line for line in makefile.split("\n") if line.startswith(".PHONY:")
        ]
        self.assertTrue(len(phony_lines) > 0)
        phony_content = " ".join(phony_lines)
        self.assertIn("driver-6.12.34+rpt-rpi-v8", phony_content)
        self.assertNotIn("quickdeploy", phony_content)


if __name__ == "__main__":
    # run the tests
    unittest.main()
