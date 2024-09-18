import os
import shutil
import subprocess
import sys


def update_pip():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def prepare_spec_files():
    shutil.copyfile("ebme.spec.TEMPLATE", "ebme.spec")

def collect_png2fts():
    import requests  # requests might only be installed after install_packages()

    if not os.path.exists("eb-png2fts"):
        os.mkdir("eb-png2fts")

    r = requests.get("https://raw.githubusercontent.com/charasyn/eb-png2fts/with-map-data/eb_png2fts.py")
    with open("eb-png2fts/eb_png2fts.py", "w") as f:
        f.write(r.text)

    r = requests.get("https://raw.githubusercontent.com/charasyn/eb-png2fts/with-map-data/image_cropper.py")
    with open("eb-png2fts/image_cropper.py", "w") as f:
        f.write(r.text)

    r = requests.get("https://raw.githubusercontent.com/charasyn/eb-png2fts/with-map-data/palettepacker.py")
    with open("eb-png2fts/palettepacker.py", "w") as f:
        f.write(r.text)

def compile_resources():
    # pyside6-rcc is not on path by default, so to be safe we'll use the full path
    full_path = os.path.join(os.path.dirname(sys.executable), "pyside6-rcc")
    try:
        subprocess.check_call([full_path, "resources.qrc", "-o", "resources_rc.py"])
    except FileNotFoundError: # not in a venv. particularly an issue for github actions
        full_path = os.path.join(os.path.dirname(sys.executable), "Scripts", "pyside6-rcc")
        subprocess.check_call([full_path, "resources.qrc", "-o", "resources_rc.py"])

if __name__ == "__main__":
    print("Updaing pip...")
    update_pip()
    print("Installing packages...")
    install_packages()
    print("Preparing .spec files...")
    prepare_spec_files()
    print("Collecting png2fts...")
    collect_png2fts()
    print("Compiling resources...")
    compile_resources()
    print("Done!")