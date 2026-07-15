@echo off
cd /d "C:\Users\86150\WorkBuddy\2026-07-14-19-08-04\lvxxiaozs"
"C:\Users\86150\.workbuddy\vendor\PortableGit\cmd\git.exe" -c http.sslVerify=false push -u origin main
echo.
echo ============================================
echo 如果提示输入用户名/密码：
echo   用户名：WangXS59
echo   密码：粘贴你的 GitHub Token (ghp_ 开头那串)
echo   （输入密码时屏幕不显示字符，属正常）
echo ============================================
echo.
pause
