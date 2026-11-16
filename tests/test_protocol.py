import unittest

from src.protocol import (
    encode_packet, decode_packet, HEADER_SIZE, MAX_PAYLOAD,
    WORKER_JOIN, TASK_DISPATCH, TASK_RESULT
)
from src.task_manager import TaskManager, hash_number
from src.client import solve


class TestProtocol(unittest.TestCase):
    def test_header_size(self):
        self.assertEqual(HEADER_SIZE, 18)

    def test_roundtrip(self):
        data = encode_packet(TASK_DISPATCH, task_id=10, worker_id=3, attempt=2, payload="10")
        packet = decode_packet(data)
        self.assertEqual(packet["type"], TASK_DISPATCH)
        self.assertEqual(packet["task_id"], 10)
        self.assertEqual(packet["worker_id"], 3)
        self.assertEqual(packet["attempt"], 2)
        self.assertEqual(packet["payload"], b"10")

    def test_empty_payload(self):
        packet = decode_packet(encode_packet(WORKER_JOIN, worker_id=1))
        self.assertEqual(packet["payload"], b"")

    def test_corrupted_payload(self):
        data = bytearray(encode_packet(TASK_RESULT, task_id=1, payload="100"))
        data[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            decode_packet(bytes(data))

    def test_bad_magic(self):
        data = b"XX" + encode_packet(WORKER_JOIN)[2:]
        with self.assertRaises(ValueError):
            decode_packet(data)

    def test_short_packet(self):
        with self.assertRaises(ValueError):
            decode_packet(b"RJ")

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            decode_packet(encode_packet(TASK_RESULT, payload="100") + b"x")

    def test_payload_too_large(self):
        with self.assertRaises(ValueError):
            encode_packet(TASK_RESULT, payload=b"x" * (MAX_PAYLOAD + 1))


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.manager = TaskManager(total=3)

    def secret(self, task_id):
        return self.manager.tasks[task_id][3]

    def test_payload_fits_limit(self):
        payload = TaskManager(total=1000).task_payload(1000)
        self.assertLessEqual(len(payload), MAX_PAYLOAD)

    def test_worker_solves_task(self):
        task_id = self.manager.get_task(1)
        payload = self.manager.task_payload(task_id).encode()
        self.assertEqual(solve(payload), self.secret(task_id))

    def test_target_matches_secret(self):
        start, end, target, secret = self.manager.tasks[1]
        self.assertTrue(start <= secret < end)
        self.assertEqual(hash_number(secret), target)

    def test_same_seed_same_tasks(self):
        self.assertEqual(TaskManager(total=5).tasks, TaskManager(total=5).tasks)

    def test_duplicate_dropped(self):
        task_id = self.manager.get_task(1)
        self.assertTrue(self.manager.save_result(task_id, 1, self.secret(task_id)))
        self.assertFalse(self.manager.save_result(task_id, 1, self.secret(task_id)))
        self.assertEqual(self.manager.duplicates, 1)

    def test_wrong_worker_rejected(self):
        task_id = self.manager.get_task(1)
        self.assertFalse(self.manager.save_result(task_id, 2, self.secret(task_id)))

    def test_wrong_result_rejected(self):
        task_id = self.manager.get_task(1)
        self.assertFalse(self.manager.save_result(task_id, 1, -1))

    def test_finished(self):
        for worker_id in (1, 2, 3):
            task_id = self.manager.get_task(worker_id)
            self.manager.save_result(task_id, worker_id, self.secret(task_id))
        self.assertTrue(self.manager.finished())
        self.assertIsNone(self.manager.get_task(1))


if __name__ == "__main__":
    unittest.main()
