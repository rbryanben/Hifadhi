from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import deleteExpiredPrivateFileAccess, resetFileUsage


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(deleteExpiredPrivateFileAccess,"interval",hours=3)
    scheduler.add_job(resetFileUsage,"interval",hours=1)
    scheduler.start()
    print("Scheduler --> Started")
