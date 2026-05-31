import json
import os
import threading
from dataclasses import dataclass
from typing import Optional

LOG_FILE = "events.log"


@dataclass
class IndexEntry:
    offset: int
    length: int

class EventStore:

    def __init__(self, log_path: str = LOG_FILE):
        self.log_path = log_path
        self._index: dict[str, IndexEntry] = {}
        self._lock = threading.Lock()

    def append(self, event: dict) -> dict:
        line: bytes = (json.dumps(event, separators=(",", ":")) + "\n").encode("utf-8")

        with self._lock:
            with open(self.log_path, "ab") as f:
                offset = f.tell()
                f.write(line)

            self._index[event["id"]] = IndexEntry(offset=offset, length=len(line))

        return event
    
    def get(self, event_id: str) -> Optional[dict]:
        entry = self._index.get(event_id)
        if entry is None:
            return None
 
        with open(self.log_path, "rb") as f:
            f.seek(entry.offset)                 
            raw = f.read(entry.length)          
 
        return json.loads(raw.decode("utf-8").strip())
        
    def list_all(self) -> list[dict]:
        """Return every event in insertion order by reading each one via 
        its index entry (still no full file scan per event).
        """
        results = []
        for event_id in self._index:
            event = self.get(event_id)
            if event:
                results.append(event)
        return results
    
    def recover(self) -> int:
        """
        Called once at server startup.
 
        Re-reads events.log line by line from the top, rebuilding the
        in-memory index from scratch.  This is how we survive a crash:
        the log is our source of truth.
 
        Returns the number of events recovered so we can log it.
        """
        if not os.path.exists(self.log_path):
            print("No existing log file found. Starting fresh.")
            return 0
 
        recovered = 0
        offset = 0
 
        with open(self.log_path, "rb") as f:
            for raw_line in f:
                length = len(raw_line)
                line = raw_line.decode("utf-8").strip()
 
                if not line:          # skip blank lines
                    offset += length
                    continue
 
                try:
                    event = json.loads(line)
                    event_id = event.get("id")
                    if event_id:
                        self._index[event_id] = IndexEntry(offset=offset, length=length)
                        recovered += 1
                except json.JSONDecodeError:
                    print(f"  ⚠️  Skipping corrupt line at offset {offset}")
 
                offset += length
 
        print(f"✅  Recovered {recovered} events from log.")
        return recovered
 
   
    def stats(self) -> dict:
        size_bytes = os.path.getsize(self.log_path) if os.path.exists(self.log_path) else 0
        return {
            "total_events": len(self._index),
            "log_file": self.log_path,
            "log_size_bytes": size_bytes,
        }
 
 
# One global instance — imported by routes.py
event_store = EventStore()
 


    
