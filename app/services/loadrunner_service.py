from __future__ import annotations

import time
import random
from pathlib import Path
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

@dataclass
class TransactionStatus:
    name: str
    response_time: float
    status: str

class LoadRunnerSignals(QObject):
    progress = Signal(int)  # percentage
    log = Signal(str)       # log message
    transaction = Signal(object) # TransactionStatus object
    finished = Signal(bool, str) # success, message

class LoadRunnerService:
    """Mock service to simulate LoadRunner scenario execution."""
    
    def __init__(self) -> None:
        pass

    def run_scenario(self, scenario_path: str, signals: LoadRunnerSignals, stop_event: list[bool]) -> None:
        """
        Simulates running a scenario.
        stop_event is a list containing a single boolean to allow checking for cancellation.
        """
        try:
            signals.log.emit(f"Starting scenario: {scenario_path}")
            signals.log.emit("Initializing Vusers...")
            time.sleep(1)
            
            if stop_event[0]:
                signals.log.emit("Execution cancelled by user.")
                signals.finished.emit(False, "Cancelled")
                return

            signals.log.emit("Vusers initialized. Starting execution.")
            total_steps = 100
            
            transactions = ["Login", "SearchProduct", "AddToCart", "Checkout", "Logout"]
            
            for i in range(total_steps):
                if stop_event[0]:
                    signals.log.emit("Execution cancelled by user.")
                    signals.finished.emit(False, "Cancelled")
                    return
                
                time.sleep(0.1) # Simulate work
                
                # Emit progress
                signals.progress.emit(i + 1)
                
                # Periodically emit logs and transactions
                if i % 5 == 0:
                    status = "Pass" if random.random() > 0.1 else "Fail"
                    tx_name = random.choice(transactions)
                    resp_time = round(random.uniform(0.1, 3.5), 2)
                    tx_status = TransactionStatus(tx_name, resp_time, status)
                    signals.transaction.emit(tx_status)
                    
                    if status == "Fail":
                        signals.log.emit(f"[ERROR] Transaction {tx_name} failed. Response time: {resp_time}s")
                    else:
                        signals.log.emit(f"[INFO] Transaction {tx_name} passed. Response time: {resp_time}s")

            signals.log.emit("Scenario execution completed successfully.")
            signals.finished.emit(True, "Completed")
            
        except Exception as e:
            signals.log.emit(f"[FATAL] Error during execution: {str(e)}")
            signals.finished.emit(False, str(e))
