import datetime
import hashlib
import socket
import sys
import threading

from .protocol import (
    encode_packet, decode_packet,
    WORKER_JOIN, HEARTBEAT, TASK_DISPATCH,
    TASK_RESULT, ACK_RESULT, STOP
)

SERVER = ("127.0.0.1", 5000)
HEARTBEAT_INTERVAL = 1.0


def log(message):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] {message}", flush=True)


def solve(payload):
    start, end, target = payload.decode().split(":")
    for number in range(int(start), int(end)):
        if hashlib.sha256(str(number).encode()).hexdigest() == target:
            return number
    return -1


def heartbeat_loop(sock, worker_id, stop):
    while not stop.wait(HEARTBEAT_INTERVAL):
        sock.sendto(encode_packet(HEARTBEAT, worker_id=worker_id), SERVER)
        log(f"SEND HEARTBEAT worker={worker_id}")


def main(worker_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(20)
    stop = threading.Event()

    try:
        sock.sendto(
            encode_packet(WORKER_JOIN, worker_id=worker_id),
            SERVER
        )
        log(f"SEND WORKER_JOIN worker={worker_id}")

        sock.sendto(
            encode_packet(HEARTBEAT, worker_id=worker_id),
            SERVER
        )
        log(f"SEND HEARTBEAT worker={worker_id}")

        threading.Thread(
            target=heartbeat_loop,
            args=(sock, worker_id, stop),
            daemon=True
        ).start()

        while True:
            try:
                data, address = sock.recvfrom(2048)
            except ConnectionResetError:
                continue

            if address != SERVER:
                continue

            try:
                packet = decode_packet(data)
            except ValueError as error:
                log(f"DROP invalid packet: {error}")
                continue

            if packet["type"] == STOP:
                log(f"RECV STOP worker={worker_id}")
                break

            if packet["type"] == ACK_RESULT:
                log(f"RECV ACK_RESULT task={packet['task_id']}")
                continue

            if packet["type"] == TASK_DISPATCH:
                task_id = packet["task_id"]
                log(f"RECV TASK_DISPATCH task={task_id}")
                result = solve(packet["payload"])

                response = encode_packet(
                    TASK_RESULT,
                    task_id=task_id,
                    worker_id=worker_id,
                    payload=str(result)
                )

                sock.sendto(response, SERVER)
                log(f"SEND TASK_RESULT task={task_id} result={result}")
    finally:
        stop.set()
        sock.close()


if __name__ == "__main__":
    main(int(sys.argv[1]))