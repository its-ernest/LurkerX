import sys
import shutil
import subprocess
import re
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
from xml.dom import minidom

from colorama import Fore


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def safe_remove(p):
    p = Path(p)
    if p.exists():
        shutil.rmtree(p) if p.is_dir() else p.unlink()


def _find_tool(name, base_dir, windows_alt=None):
    in_path = shutil.which(name)
    if in_path:
        return Path(in_path)
    local = base_dir / (windows_alt or name)
    if local.exists():
        return local
    raise FileNotFoundError(f"Required tool not found: {name}")


def _update_manifest_label(manifest_path: Path, app_name: str):
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    ns = {
        "android": "http://schemas.android.com/apk/res/android",
    }

    target_activity = None
    for activity in root.findall(".//activity", ns):
        has_main_launcher = False
        for intent_filter in activity.findall("intent-filter", ns):
            for action in intent_filter.findall("action", ns):
                if action.get(f"{{{ns['android']}}}name") == "android.intent.action.MAIN":
                    has_main_launcher = True
            for category in intent_filter.findall("category", ns):
                if category.get(f"{{{ns['android']}}}name") == "android.intent.category.LAUNCHER":
                    has_main_launcher = True
        if has_main_launcher:
            target_activity = activity
            break

    if target_activity is None:
        activities = root.findall(".//activity", ns)
        if activities:
            target_activity = activities[0]

    if target_activity is not None:
        target_activity.set(f"{{{ns['android']}}}label", app_name)
        _write_manifest(tree, manifest_path)


def _update_strings_app_name(work_dir: Path, app_name: str) -> bool:
    strings_candidates = [
        work_dir / "res" / "values" / "strings.xml",
        work_dir / "res" / "values-en" / "strings.xml",
        work_dir / "res" / "values-en-rUS" / "strings.xml",
    ]

    for strings_path in strings_candidates:
        if not strings_path.exists():
            continue

        tree = ET.parse(strings_path)
        root = tree.getroot()

        updated = False
        for elem in root.iter("string"):
            if elem.get("name") == "app_name":
                elem.text = app_name
                updated = True
                break

        if updated:
            rough_string = ET.tostring(root, encoding="utf-8")
            reparsed = minidom.parseString(rough_string)
            pretty = reparsed.toprettyxml(indent="    ", encoding="utf-8")
            text = pretty.decode("utf-8")
            lines = text.splitlines()
            cleaned = []
            for line in lines:
                stripped = line.strip()
                if stripped == "" or stripped == '<?xml version="1.0" ?>':
                    continue
                cleaned.append(line)
            strings_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
            print(f"{Fore.GREEN}[+]{Fore.RESET} Updated app_name in {strings_path}")
            return True

    return False


def _write_manifest(tree, manifest_path: Path):
    rough_string = ET.tostring(tree.getroot(), encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="    ", encoding="utf-8")
    text = pretty.decode("utf-8")
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped == '<?xml version="1.0" ?>':
            continue
        cleaned.append(line)
    manifest_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")


def modify_apk(
    app_name: str,
    app_icon: Path,
    server_url: str,
    base_apk: Path,
    keystore: Path,
    keystore_pass: str,
    key_password: str,
    keystore_alias: str | None,
    base_dir: Path,
):
    apktool = _find_tool("apktool", base_dir, "apktool.bat" if platform.system() == "Windows" else "apktool")
    zipalign = _find_tool("zipalign", base_dir / "build-tools" / "35.0.1", "zipalign.exe" if platform.system() == "Windows" else "zipalign")
    apksigner = _find_tool("apksigner", base_dir / "build-tools" / "35.0.1", "apksigner.bat" if platform.system() == "Windows" else "apksigner")

    work_dir = base_dir / "workdir"
    output_apk = base_dir / "result" / "final.apk"

    print(f"{Fore.YELLOW}[+]{Fore.RESET} Modifying APK: {Fore.GREEN}{app_name}{Fore.RESET}")

    safe_remove(work_dir)
    if not base_apk.exists():
        raise FileNotFoundError(f"Base APK not found: {base_apk}")

    run([apktool, "d", base_apk, "-o", work_dir, "-f", "--no-crunch"])

    for d in ["mipmap-hdpi", "mipmap-mdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]:
        target = work_dir / "res" / d / "ic_launcher.png"
        if target.exists():
            shutil.copy2(app_icon, target)

    manifest = work_dir / "AndroidManifest.xml"
    if manifest.exists():
        if not _update_strings_app_name(work_dir, app_name):
            _update_manifest_label(manifest, app_name)

    apk_assets = work_dir / "assets"
    src_choices = base_dir / "choices.ini"
    if apk_assets.exists() and src_choices.exists():
        dest = apk_assets / "choices.ini"
        shutil.copy2(src_choices, dest)
        print(f"{Fore.GREEN}[+]{Fore.RESET} Replaced choices.ini in APK assets")

    run([apktool, "b", work_dir, "-o", output_apk])

    aligned = output_apk.with_name("final_aligned.apk")
    signed = output_apk.with_name("final_signed.apk")
    safe_remove(aligned)
    safe_remove(signed)

    run([zipalign, "-v", "4", output_apk, aligned])

    sign_cmd = [
        apksigner, "sign",
        "--ks", keystore,
        "--ks-pass", f"pass:{keystore_pass}",
        "--out", signed,
        aligned
    ]

    if key_password:
        sign_cmd[3:3] = ["--key-pass", f"pass:{key_password}"]

    if keystore_alias:
        sign_cmd[3:3] = ["--ks-key-alias", keystore_alias]

    run(sign_cmd)

    return signed
