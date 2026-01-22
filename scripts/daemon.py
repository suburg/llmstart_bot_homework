#!/usr/bin/env python3
"""
Кроссплатформенный скрипт для управления ботом в фоновом режиме.
Поддерживает Windows и Linux (systemd, nohup).
"""

import os
import sys
import signal
import subprocess
import platform
from pathlib import Path

PID_FILE = Path(".bot.pid")
LOG_FILE = Path("logs/bot.log")


def is_process_running(pid: int) -> bool:
    """Проверяет, запущен ли процесс с данным PID."""
    try:
        if platform.system() == "Windows":
            # Windows: используем tasklist
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            )
            return str(pid) in result.stdout
        else:
            # Linux/Unix: отправляем сигнал 0
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.SubprocessError):
        return False


def start_bot():
    """Запускает бота в фоновом режиме."""
    # Проверяем, не запущен ли уже бот
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_process_running(pid):
                print(f"Bot is already running (PID: {pid})")
                return
            else:
                print("Removing stale PID file...")
                PID_FILE.unlink()
        except (ValueError, OSError) as e:
            print(f"Warning: Invalid PID file: {e}")
            PID_FILE.unlink(missing_ok=True)

    # Создаем директорию для логов
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Запускаем бота в зависимости от ОС
    if platform.system() == "Windows":
        # Windows: используем CREATE_NEW_PROCESS_GROUP и DETACHED_PROCESS
        import subprocess
        
        # Запускаем процесс в фоновом режиме
        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "src.main"],
            stdout=open(LOG_FILE, "a"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
        pid = process.pid
    else:
        # Linux: используем nohup
        process = subprocess.Popen(
            ["nohup", "uv", "run", "python", "-m", "src.main"],
            stdout=open(LOG_FILE, "a"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,  # Создаем новую группу процессов
        )
        pid = process.pid

    # Сохраняем PID
    PID_FILE.write_text(str(pid))
    print(f"Bot started with PID: {pid}")
    print(f"Logs: {LOG_FILE.absolute()}")


def stop_bot():
    """Останавливает бота."""
    if not PID_FILE.exists():
        print("Bot is not running (.bot.pid not found)")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        print("Error: Invalid PID file")
        PID_FILE.unlink()
        return

    if not is_process_running(pid):
        print("Bot is not running (stale PID file)")
        PID_FILE.unlink()
        return

    # Останавливаем процесс
    try:
        if platform.system() == "Windows":
            # Windows: используем taskkill
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
        else:
            # Linux: отправляем SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            # Ждем завершения процесса
            import time
            for _ in range(10):
                if not is_process_running(pid):
                    break
                time.sleep(0.5)
            else:
                # Если не завершился, используем SIGKILL
                print("Process didn't terminate, sending SIGKILL...")
                os.kill(pid, signal.SIGKILL)
        
        print(f"Bot stopped (PID: {pid})")
        PID_FILE.unlink()
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"Error stopping bot: {e}")


def check_status():
    """Проверяет статус бота."""
    if not PID_FILE.exists():
        print("Bot is not running")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        print("Error: Invalid PID file")
        PID_FILE.unlink()
        return

    if is_process_running(pid):
        print(f"Bot is running (PID: {pid})")
    else:
        print("Bot is not running (stale PID file)")
        PID_FILE.unlink()


def main():
    if len(sys.argv) != 2:
        print("Usage: python daemon.py {start|stop|status}")
        sys.exit(1)

    command = sys.argv[1].lower()
    
    if command == "start":
        start_bot()
    elif command == "stop":
        stop_bot()
    elif command == "status":
        check_status()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python daemon.py {start|stop|status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
