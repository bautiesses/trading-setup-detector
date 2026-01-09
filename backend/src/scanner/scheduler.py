"""
Scanner Scheduler - Automatic scanning with APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional, Dict, List
import asyncio

from src.database import AsyncSessionLocal
from src.scanner.service import ScannerService
from src.watchlist.models import WatchlistItem
from sqlalchemy import select


class ScannerScheduler:
    """Manages automatic scanning for all users"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.interval_minutes = 5
        self.last_scan_time: Optional[datetime] = None
        self.new_signals: Dict[int, List[dict]] = {}  # user_id -> list of new signals
        self._lock = asyncio.Lock()

    def start(self, interval_minutes: int = 5):
        """Start the automatic scanner"""
        if self.is_running:
            return

        self.interval_minutes = interval_minutes

        # Add job to run scans
        self.scheduler.add_job(
            self._run_scan_for_all_users,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='auto_scanner',
            replace_existing=True,
            max_instances=1
        )

        # Only start scheduler if not already running
        if not self.scheduler.running:
            self.scheduler.start()

        self.is_running = True
        print(f"[Scanner] Started automatic scanning every {interval_minutes} minutes")

    def stop(self):
        """Stop the automatic scanner"""
        if not self.is_running:
            return

        try:
            self.scheduler.remove_job('auto_scanner')
        except Exception:
            pass  # Job might not exist

        self.is_running = False
        print("[Scanner] Stopped automatic scanning")

    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_scan": self.last_scan_time.isoformat() if self.last_scan_time else None
        }

    async def get_new_signals(self, user_id: int) -> List[dict]:
        """Get and clear new signals for a user"""
        async with self._lock:
            signals = self.new_signals.pop(user_id, [])
            return signals

    async def _run_scan_for_all_users(self):
        """Run scan for all users with active watchlists"""
        print(f"[Scanner] Running automatic scan at {datetime.now()}")

        async with AsyncSessionLocal() as db:
            try:
                # Get all unique user IDs with active watchlist items
                result = await db.execute(
                    select(WatchlistItem.user_id)
                    .where(WatchlistItem.is_active == True)
                    .distinct()
                )
                user_ids = [row[0] for row in result.fetchall()]

                for user_id in user_ids:
                    try:
                        service = ScannerService(db)
                        results = await service.run_scan(user_id=user_id)

                        if results:
                            # Store new signals for this user
                            async with self._lock:
                                if user_id not in self.new_signals:
                                    self.new_signals[user_id] = []

                                for r in results:
                                    self.new_signals[user_id].append({
                                        "id": r.id,
                                        "symbol": r.symbol,
                                        "timeframe": r.timeframe,
                                        "pattern_type": r.pattern_type,
                                        "level_price": r.level_price,
                                        "current_price": r.current_price,
                                        "message": r.message,
                                        "created_at": r.created_at.isoformat()
                                    })

                            print(f"[Scanner] Found {len(results)} signals for user {user_id}")

                    except Exception as e:
                        print(f"[Scanner] Error scanning for user {user_id}: {e}")
                        continue

                self.last_scan_time = datetime.now()

            except Exception as e:
                print(f"[Scanner] Error in automatic scan: {e}")


# Global scheduler instance
scanner_scheduler = ScannerScheduler()
