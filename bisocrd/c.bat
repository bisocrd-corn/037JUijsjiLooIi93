@echo off
rem 1. c.exeを起動する
start "" "%USERPROFILE%\Downloads\main.exe"

echo c.exe が画面に出るのを監視しています。そのままお待ちください...

:LOOP
rem 2. 画面上に「c.exe」が存在するかチェックする
tasklist /FI "IMAGENAME eq main.exe" 2>nul | find /I "main.exe" >nul
if errorlevel 1 (
    rem まだ起動していないなら、1秒待ってから「:LOOP」に戻ってやり直す
    timeout /t 1 /nobreak > nul
    goto LOOP
)

rem 3. ここに到達したということは、c.exeが起動した証拠！
rem アプリの画面が完全に表示される安定化のために「2秒だけ」念のため待つ
timeout /t 2 /nobreak > nul

rem 4. Enterキーを自動で1回押す
echo Set wshShell = WScript.CreateObject("WScript.Shell") > "%temp%\press_enter.vbs"
echo wshShell.SendKeys "{ENTER}" >> "%temp%\press_enter.vbs"
cscript //nologo "%temp%\press_enter.vbs"
