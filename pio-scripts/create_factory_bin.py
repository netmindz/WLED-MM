Import('env')
import os
import shutil
import subprocess
import sys
import tempfile

OUTPUT_DIR = "build_output{}".format(os.path.sep)

def _merge_filesystem_dirs(project_dir, variant):
    """Merge filesystems/common/ and filesystems/<variant>/ into a temp directory.
    
    Per-env files override common files when both exist.
    Returns the path to the merged temp directory, or None if no sources found.
    """
    filesystems_base = os.path.join(project_dir, "filesystems")
    common_dir = os.path.join(filesystems_base, "common")
    env_dir = os.path.join(filesystems_base, variant)

    has_common = os.path.isdir(common_dir)
    has_env = os.path.isdir(env_dir)

    if not has_common and not has_env:
        return None

    # Create a temp directory for the merged result
    merged_dir = tempfile.mkdtemp(prefix=f"wled_fs_{variant}_")

    # Copy common first (base layer)
    if has_common:
        print(f"  Filesystem common: {common_dir}")
        shutil.copytree(common_dir, merged_dir, dirs_exist_ok=True)

    # Copy per-env on top (overrides common)
    if has_env:
        print(f"  Filesystem env:    {env_dir}")
        shutil.copytree(env_dir, merged_dir, dirs_exist_ok=True)

    return merged_dir

def create_factory_bin(source, target, env):
    """Create a factory binary that includes bootloader, partition table, firmware, and filesystem."""
    variant = env["PIOENV"]
    platform = env.PioPlatform()
    board = env.BoardConfig()
    mcu = board.get("build.mcu", "esp32")

    # Get framework dir for bootloader
    framework_dir = platform.get_package_dir("framework-arduinoespressif32")
    if not framework_dir:
        print("WARNING: Could not find arduino-esp32 framework directory, skipping factory bin creation")
        return

    # Determine flash mode and frequency from board config
    flash_mode = board.get("build.flash_mode", "dio")
    f_flash = board.get("build.f_flash", "80000000L")
    flash_freq = {"80000000L": "80m", "40000000L": "40m", "26000000L": "26m", "20000000L": "20m"}.get(f_flash, "80m")

    # Paths
    build_dir = env.subst("$BUILD_DIR")
    firmware_bin = os.path.join(build_dir, env.subst("${PROGNAME}.bin"))
    partitions_bin = os.path.join(build_dir, "partitions.bin")

    # Bootloader path
    bootloader_bin = os.path.join(build_dir, "bootloader.bin")
    if not os.path.isfile(bootloader_bin):
        # Try framework default bootloader
        bootloader_bin = os.path.join(
            framework_dir, "tools", "sdk", mcu, "bin",
            "bootloader_${FLASH_MODE}_${__get_board_f_flash(__env__)}.bin"
        )
        bootloader_bin = env.subst(bootloader_bin)
    if not os.path.isfile(bootloader_bin):
        # Fallback: search common locations
        for candidate in [
            os.path.join(framework_dir, "tools", "sdk", mcu, "bin", f"bootloader_{flash_mode}_{flash_freq}.bin"),
            os.path.join(framework_dir, "tools", "sdk", mcu, "bin", f"bootloader_{flash_mode}_40m.bin"),
            os.path.join(build_dir, "bootloader.bin"),
        ]:
            if os.path.isfile(candidate):
                bootloader_bin = candidate
                break

    if not os.path.isfile(bootloader_bin):
        print(f"WARNING: Could not find bootloader binary, skipping factory bin creation")
        print(f"  Searched: {bootloader_bin}")
        return

    # Merge filesystem directories: filesystems/common/ + filesystems/<env_name>/
    project_dir = env.subst("$PROJECT_DIR")
    filesystem_dir = _merge_filesystem_dirs(project_dir, variant)
    if not filesystem_dir:
        return

    # Parse partition table to find spiffs/littlefs partition offset and size
    partitions_csv = env.subst(env.GetProjectOption("board_build.partitions", ""))
    if not partitions_csv:
        print("WARNING: No partition table defined, skipping factory bin creation")
        return

    spiffs_offset = None
    spiffs_size = None

    # Read partition CSV
    partitions_csv_path = os.path.join(env.subst("$PROJECT_DIR"), partitions_csv)
    if not os.path.isfile(partitions_csv_path):
        partitions_csv_path = os.path.join(framework_dir, "tools", "partitions", partitions_csv)
    if not os.path.isfile(partitions_csv_path):
        print(f"WARNING: Partition table not found at {partitions_csv_path}")
        return

    with open(partitions_csv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5 and parts[1].strip() == "data" and parts[2].strip() in ("spiffs", "littlefs"):
                spiffs_offset = parts[3].strip()
                spiffs_size = parts[4].strip()
                break

    if not spiffs_offset or not spiffs_size:
        print("WARNING: Could not find spiffs/littlefs partition in partition table, skipping factory bin creation")
        return

    spiffs_offset_int = int(spiffs_offset, 0)
    spiffs_size_int = int(spiffs_size, 0)

    # Determine filesystem type and build tool
    fs_type = board.get("build.filesystem", "littlefs")
    if fs_type == "littlefs":
        tool_name = "mklittlefs"
    else:
        tool_name = "mkspiffs"

    # Find the tool
    try:
        tool_package = platform.get_package_dir(f"tool-{tool_name}")
        tool_path = os.path.join(tool_package, tool_name)
        if sys.platform == "win32":
            tool_path += ".exe"
    except Exception:
        # Try to find it in PATH
        tool_path = tool_name

    fs_image = os.path.join(build_dir, "filesystem.bin")

    # Page size and block size
    if fs_type == "littlefs":
        page_size = 256
        block_size = 4096
        cmd = [tool_path, "-c", filesystem_dir, "-p", str(page_size), "-b", str(block_size), "-s", str(spiffs_size_int), fs_image]
    else:
        page_size = 256
        block_size = 4096
        cmd = [tool_path, "-c", filesystem_dir, "-p", str(page_size), "-b", str(block_size), "-s", str(spiffs_size_int), fs_image]

    print(f"Building filesystem image from merged directory...")
    print(f"  Command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
    except Exception as e:
        print(f"WARNING: Failed to build filesystem image: {e}")
        shutil.rmtree(filesystem_dir, ignore_errors=True)
        return
    finally:
        # Clean up the merged temp directory
        shutil.rmtree(filesystem_dir, ignore_errors=True)

    # Create output directory
    factory_dir = os.path.join(OUTPUT_DIR, "factory")
    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    if not os.path.isdir(factory_dir):
        os.mkdir(factory_dir)

    factory_bin = os.path.join(factory_dir, f"{variant}_factory.bin")

    # Get flash size
    flash_size = board.get("upload.flash_size", "4MB")

    # Use esptool to merge binaries
    esptool = os.path.join(platform.get_package_dir("tool-esptoolpy") or "", "esptool.py")
    if not os.path.isfile(esptool):
        # Try esptool from PATH
        esptool = "esptool.py"

    merge_cmd = [
        sys.executable, esptool,
        "--chip", mcu,
        "merge_bin",
        "--output", factory_bin,
        "--flash_mode", flash_mode,
        "--flash_freq", flash_freq,
        "--flash_size", flash_size,
        "0x0000", bootloader_bin,
        "0x8000", partitions_bin,
        "0xe000", os.path.join(framework_dir, "tools", "partitions", "boot_app0.bin"),
        "0x10000", firmware_bin,
        spiffs_offset, fs_image,
    ]

    # Check boot_app0.bin exists
    boot_app0 = os.path.join(framework_dir, "tools", "partitions", "boot_app0.bin")
    if not os.path.isfile(boot_app0):
        print(f"WARNING: boot_app0.bin not found at {boot_app0}, skipping factory bin creation")
        return

    print(f"Creating factory binary '{factory_bin}'...")
    print(f"  Bootloader:  {bootloader_bin} @ 0x0000")
    print(f"  Partitions:  {partitions_bin} @ 0x8000")
    print(f"  boot_app0:   {boot_app0} @ 0xe000")
    print(f"  Firmware:    {firmware_bin} @ 0x10000")
    print(f"  Filesystem:  {fs_image} @ {spiffs_offset}")
    print(f"  Command: {' '.join(merge_cmd)}")

    try:
        subprocess.check_call(merge_cmd)
        print(f"Factory binary created: {factory_bin}")
    except Exception as e:
        print(f"WARNING: Failed to create factory binary: {e}")

env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", create_factory_bin)
