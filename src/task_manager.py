from collections import deque
class TaskManager:
    def __init__(self, total=1000):
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

    def save_result(self, task_id, worker_id, result):
        if task_id in self.results:
            self.duplicates += 1
            return False

        if self.assigned.get(task_id) != worker_id:
            return False

        if result != task_id * task_id:
            return False

        self.results[task_id] = result
        return True

    def finished(self):
        return len(self.results) == self.total