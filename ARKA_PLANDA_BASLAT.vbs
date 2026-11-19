Set WshShell = CreateObject("WScript.Shell")
strProjectPath = "C:\Users\user\Desktop\GitHub Project\Finance Project"
pythonExe = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"

' Arka planda sessizce supervisor.py servisini başlat
WshShell.Run "cmd.exe /c cd /d """ & strProjectPath & """ && """ & pythonExe & """ core\supervisor.py", 0, False
