import hashlib
import random
from collections import deque

RANGE_SIZE = 20000


def hash_number(number):
    return hashlib.sha256(str(number).encode()).hexdigest()


class TaskManager:
    def __init__(self, total=1000, seed=17):
        rng = random.Random(seed)
        self.tasks = {}
        for task_id in range(1, total + 1):
            start = (task_id - 1) * RANGE_SIZE
            secret = start + rng.randrange(RANGE_SIZE)
            self.tasks[task_id] = (start, start + RANGE_SIZE, hash_number(secret), secret)
        self.pending = deque(range(1, total + 1))
        self.results = {}
        self.assigned = {}
        self.total = total
        self.duplicates = 0

    def get_task(self, worker_id):
        if not self.pending:
            return None

        task_id = self.pending.popleft()
        self.assigned[task_id] = worker_id
        return task_id

    def task_payload(self, task_id):
        start, end, target, _ = self.tasks[task_id]
        return f"{start}:{end}:{target}"

    def save_result(self, task_id, worker_id, result):
        if task_id in self.results:
            self.duplicates += 1
            return False

        if self.assigned.get(task_id) != worker_id:
            return False

        if result != self.tasks[task_id][3]:
            return False

        self.results[task_id] = result
        return True

    def finished(self):
        return len(self.results) == self.total
