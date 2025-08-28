'Дополнительный скрипт для запуска run.bat без консоли

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c run.bat", 0, True
Set WshShell = Nothing
