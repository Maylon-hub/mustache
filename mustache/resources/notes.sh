
# Problem: include errors detected. Please update your includePath. Squiggles are disabled for this translation unit (C:\Users\Gamer\Documents\GitHub\mustache\mustache\resources\hai.c).C/C++(1696)
# cannot open source file "Python.h"C/C++(1696)

# Copilot: On Windows, ensure Python development headers are installed and update the include path:

# Replace <PythonInstallDir> with the actual Python installation directory.

# Example: C:\Python39\include


# Add the include path to your compiler settings:

# For Visual Studio Code, add the following to your c_cpp_properties.json file:

# {

#   "configurations": [

#     {

#       "name": "Win32",

#       "includePath": [

#         "<PythonInstallDir>\\include",

#         "<PythonInstallDir>\\libs"

#       ],

#       ...

#     }

#   ]

# }



# Alternatively, if using GCC/Clang, add the include path during compilation:

# gcc -I"<PythonInstallDir>/include" -L"<PythonInstallDir>/libs" -o hai hai.c -lpython3.9
