import os
import subprocess
import shutil
import clang.cindex

# Test for existence of llvm on system
if shutil.which("llvm-config") is None:
    raise RuntimeError("Illuminate Clang Config Error: llvm-config not found on path.")

# Find libclang.so or .dll
clang_libdir = subprocess.check_output(['llvm-config', '--libdir']).decode().rstrip('\r\n')

libclang, *other = [lib for lib in os.listdir(clang_libdir) if lib.startswith('libclang.') and (lib.endswith('so') or lib.endswith('dll'))]

if libclang == "":
    raise RuntimeError("Illuminate Clang Config Error: libclang dynlib not found!")

clang.cindex.Config.set_library_file(os.path.join(clang_libdir, libclang))
