SET F=".\dist"
IF EXIST %F% RMDIR /S /Q %F%

pyinstaller --clean --onefile --specpath .\build --name "Underwatch Ultimate" --noconsole underwatch.py 
pyinstaller --clean --onefile --specpath .\build --name "Underwatch Ultimate (With Console)" underwatch.py
xcopy .\templates .\dist\templates\

RMDIR /S /Q ".\build"
PAUSE