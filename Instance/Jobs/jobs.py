


"""
    Deletes all expired signatures after an hour
"""
def deleteExpiredPrivateFileAccess():
    from Shared.models import ipv4Access, presignedURL
    import datetime, pytz

    utc = pytz.UTC
    current_time = datetime.datetime.now().replace(tzinfo=utc)

    presignedURL.objects.filter(expires__lte=current_time).delete()
    ipv4Access.objects.filter(expires__lte=current_time).delete()
    print("Job --> Cleaned out expired private file access")