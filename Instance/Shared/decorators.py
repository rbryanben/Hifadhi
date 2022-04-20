"""
    POST Decorator -> Allow only post methods
"""
def PostOnly(func,*args,**kwargs):
    def inner(*args,**kwargs):
        print(kwargs.get("request"))
        return func(*args,**kwargs)

    return inner
