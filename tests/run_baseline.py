import subprocess
import sys
import time
from pathlib import Path

LOGS = Path("logs")
LOGS.mkdir(exist_ok=True)


def main():
    processes = []
    files = []

    try:
        server_log = open(LOGS / "server.log", "w")
        files.append(server_log)

        server = subprocess.Popen(
            [sys.executable, "-u", "-m", "src.server"],
            stdout=server_log,
            stderr=subprocess.STDOUT
        )
        processes.append(server)

        time.sleep(0.5)

        for worker_id in range(1, 5):
            log_file = open(
                LOGS / f"worker_{worker_id}.log", "w"
            )
            files.append(log_file)

            worker = subprocess.Popen(
                [
                    sys.executable, "-u",
                    "-m", "src.client",
                    str(worker_id)
                ],
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            processes.append(worker)

        for process in processes:
            process.wait(timeout=30)

        for file in files:
            file.flush()

        output = (LOGS / "server.log").read_text()

        success = (
            all(p.returncode == 0 for p in processes)
            and "COMPLETED=1000" in output
            and "DUPLICATES=0" in output
            and "BASELINE PASS" in output
        )

        if success:
            print("PASS: 4 workers, 1000 tasks, 0 duplicates")
        else:
            print("FAIL: Check the files in logs/")
            sys.exit(1)

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for file in files:
            file.close()


if __name__ == "__main__":
    main()