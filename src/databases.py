from datetime import datetime, timezone

from sortedcontainers import SortedList


class TransactionsDB:
    def __init__(self):
        self._db: SortedList = SortedList()

    def add(self, datetime_str: str, amount: str = None):
        self._db.add(self._datetime_str_to_number(datetime_str))

    def summary(self, start_datetime_str: str, end_datetime_str: str):
        start = self._datetime_str_to_number(start_datetime_str)
        end = self._datetime_str_to_number(end_datetime_str)
        n = self._db.bisect_left(end) - self._db.bisect_left(start)
        return (n * 19.9, n)

    @classmethod
    def _datetime_str_to_number(cls, datetime_str: str) -> int:
        if "." in datetime_str:
            dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        value = int(dt.timestamp() * 1000)
        return value
