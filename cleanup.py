from pathlib import Path
import shutil

movefiles = [
    Path("src/telem.py"),
    Path("src/mainwindow.py"),
    Path("src/metadata_v2.py"),
    Path("src/worker.py"),
]
delfiles = [
    Path("src/telem.py"),
    Path("src/mainwindow.py"),
    Path("src/metadata_v2.py"),
    Path("src/worker.py"),
    Path("src/telem.c"),
    Path("src/mainwindow.c"),
    Path("src/metadata_v2.c"),
    Path("src/worker.c"),
]

dumpfolder = Path("build")

for file in movefiles:
    shutil.copy(file, dumpfolder)

for file in delfiles:
    file.unlink()
