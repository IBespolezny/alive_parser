import asyncio
import logging
from pathlib import Path
import asyncio.subprocess

# -------------------- Настройки --------------------
CATALOG_CMD = ["python", "-u", "main.py"]
DETAIL_CMD = ["python", "-u", "detail_worker.py"]
LAST_PAGE_FILE = Path("last_page.txt")
DETAIL_WORKER_TIMEOUT_HOURS = 10  # ограничение работы DetailWorker

# -------------------- Логирование --------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("runner")

# -------------------- Функция запуска процесса асинхронно --------------------
async def run_process(cmd, name, monitor_output=None, timeout=None):
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        logger.info(f"[{name}] Запущен процесс: {' '.join(cmd)}")

        start_time = asyncio.get_event_loop().time()

        while True:
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                logger.warning(f"[{name}] Таймаут превышен, убиваем процесс")
                process.kill()
                await process.wait()
                return False

            stdout_line = await process.stdout.readline()
            stderr_line = await process.stderr.readline()

            if stdout_line:
                try:
                    line = stdout_line.decode(errors='ignore').strip()
                except Exception:
                    line = stdout_line.decode('latin-1', errors='ignore').strip()
                print(f"[{name}] {line}", flush=True)
                if monitor_output and monitor_output(line):
                    logger.info(f"[{name}] Условие завершения выполнено, завершаем процесс")
                    process.terminate()
                    await process.wait()
                    return True

            if stderr_line:
                try:
                    err_line = stderr_line.decode(errors='ignore').strip()
                except Exception:
                    err_line = stderr_line.decode('latin-1', errors='ignore').strip()
                print(f"[{name} ERR] {err_line}", flush=True)

            if process.stdout.at_eof() and process.stderr.at_eof():
                break

        retcode = await process.wait()
        if retcode == 0:
            logger.info(f"[{name}] Процесс завершился успешно")
            return True
        else:
            logger.warning(f"[{name}] Процесс завершился с ошибкой (код {retcode})")
            return False

    except Exception as e:
        logger.exception(f"[{name}] Ошибка при запуске процесса: {e}")
        return False

# -------------------- Основной runner --------------------
async def runner_loop():
    first_run = True

    while True:
        # Всегда начинаем с main.py, если первый запуск или detail_worker завершился
        logger.info("[Runner] Запускаем main.py (обход каталога)")
        await run_process(CATALOG_CMD, "Catalog", monitor_output=lambda line: 'Main loop exited' in line)

        # После завершения main.py проверяем наличие last_page.txt
        if LAST_PAGE_FILE.exists():
            logger.info("[Runner] Обнаружен файл last_page.txt — продолжаем обход каталога")
            await asyncio.sleep(5)
            continue

        # Если файла нет — запускаем detail_worker.py
        logger.info("[Runner] Файл last_page.txt не найден — запускаем detail_worker.py")
        await run_process(
            DETAIL_CMD,
            "DetailWorker",
            monitor_output=lambda line: 'Нет задач для парсинга' in line or 'DetailWorker завершил работу' in line,
            timeout=DETAIL_WORKER_TIMEOUT_HOURS * 3600,
        )

        first_run = False
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(runner_loop())