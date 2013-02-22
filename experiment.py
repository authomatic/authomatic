import datetime
import time
import threading

start_time = datetime.datetime.now()

def func(value):
    print 'START: {} {}'.format(value, datetime.datetime.now())
    time.sleep(5)
    print 'END: {} {}'.format(value, datetime.datetime.now())
    return str(value) * 10


class MyThread(threading.Thread):
    
    def __init__(self, func, args=(), kwargs={}):
        
        super(MyThread, self).__init__()
        
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
        self.result = None
    
    def run(self):
        self.result = self.func(*self.args, **self.kwargs)
    
    def get_result(self):
        self.join()
        return self.result

def run_async(*args, **kwargs):
    t = MyThread(*args, **kwargs)
    t.start()
    return t

t1 = run_async(func=func, args=(1,))
t2 = run_async(func=func, args=(2,))
t3 = run_async(func=func, args=(3,))

print '\n'
print 'Do other stuff...'
print '\n'

print t1.get_result()
print t2.get_result()
print t3.get_result()

print '=' * 70
print 'Duration: {}'.format(datetime.datetime.now() - start_time)