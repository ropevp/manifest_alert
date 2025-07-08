Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the script directory
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Build the command to run pythonw.exe silently
strCommand = """" & strScriptDir & "\.venv\Scripts\pythonw.exe"" """ & strScriptDir & "\main.py"""

' Run the command silently (0 = hidden window, False = don't wait)
objShell.Run strCommand, 0, False
