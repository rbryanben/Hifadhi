from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import deleteExpiredPrivateFileAccess


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(deleteExpiredPrivateFileAccess,"interval",hours=3)
    scheduler.start()
    print("Scheduler --> Started")
