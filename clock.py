from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import time

sched = BlockingScheduler()

@sched.scheduled_job('interval', hours=2)
def keep_alive():
    """Ping your app to keep it alive"""
    try:
        # Replace with your actual app URL after deployment
        requests.get('https://your-app.onrender.com/health')
        print(f"Keep-alive ping sent at {time.ctime()}")
    except:
        print("Keep-alive ping failed")

if __name__ == '__main__':
    sched.start()