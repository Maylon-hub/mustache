@echo off
call "D:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
set DISTUTILS_USE_SDK=1
"d:\GitHub\mustache\.venv\Scripts\pip.exe" install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mustache-core==0.1.0
