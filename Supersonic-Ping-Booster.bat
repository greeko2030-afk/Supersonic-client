@echo off
title Supersonic Network & Ping Optimizer
color 0b
echo ===================================================
echo     SUPERSONIC CLIENT - PING MAX OPTIMIZATION
echo ===================================================
echo Optimizing Windows TCP/IP for 0 Ping on Minecraft...

:: Network Throttling Index Disable
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f >nul

:: TCP NoDelay and Ack Frequency Tweaks
for /f "tokens=3*" %%i in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkCards" /s ^| findstr /i "ServiceName"') do (
    reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\%%i" /v TCPNoDelay /t REG_DWORD /d 1 /f >nul
    reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\%%i" /v TcpAckFrequency /t REG_DWORD /d 1 /f >nul
)

:: Flush DNS
ipconfig /flushdns >nul

echo [SUCCESS] Network Optimized!
echo Launching Supersonic Client...
timeout /t 2 >nul

:: Launching the actual launcher automatically
start "" "Supersonic-Launcher.exe"
exit
