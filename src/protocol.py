import struct
import zlib

MAGIC = b"RJ"
VERSION = 1

WORKER_JOIN = 1
HEARTBEAT = 2
TASK_DISPATCH = 3
TASK_RESULT = 4
ACK_RESULT = 5
STOP = 6

FORMAT = "!2sBBIHHHI"
HEADER_SIZE = struct.calcsize(FORMAT)
MAX_PAYLOAD = 512


def encode_packet(msg_type, task_id=0, worker_id=0,
                  attempt=1, payload=b""):
    if isinstance(payload, str):
        payload = payload.encode()

    if len(payload) > MAX_PAYLOAD:
        raise ValueError("Payload exceeds 512 bytes")

    checksum = zlib.crc32(payload)

    header = struct.pack(
        FORMAT, MAGIC, VERSION, msg_type,
        task_id, worker_id, attempt,
        len(payload), checksum
    )
    return header + payload


def decode_packet(data):
    if len(data) < HEADER_SIZE:
        raise ValueError("Packet too short")

    fields = struct.unpack(FORMAT, data[:HEADER_SIZE])
    magic, version, msg_type, task_id, worker_id, \
        attempt, length, checksum = fields

    payload = data[HEADER_SIZE:]

    if magic != MAGIC or version != VERSION:
        raise ValueError("Invalid protocol")

    if length != len(payload) or length > MAX_PAYLOAD:
        raise ValueError("Invalid payload length")

    if zlib.crc32(payload) != checksum:
        raise ValueError("Checksum mismatch")

    return {
        "type": msg_type,
        "task_id": task_id,
        "worker_id": worker_id,
        "attempt": attempt,
        "payload": payload
    }
