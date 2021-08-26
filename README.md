Because backing up data is never redundant.
# Viblo Exporter

## Introduction
Are you tired of Viblo going down all the time? Did you make the mistake of uploading your precious working notes there hoping for 24/7 access? Well, sucks to be you who doesn't at least have an offline copy of whatever.

That `you` described above is me. Yes, sucks to be me.

## Installation
Clone and run.

```python
python app.py
```

This will run on port `$PORT` (if environment variable not exists, fallback to 5000). Note that you need to change the WebSocket protocol to `ws://` if the domain is not secure (i.e. HTTPS).

This repo is also ready to be deployed to Heroku. Even though it works fine locally, but runs into some trouble when deployed as noted below.

## Notes
The demo is running on https://viblo-exporter.herokuapp.com, but it doesn't work due to CloudFlare blocking our API calls as DDoS attacks. If anyone got a fix/bypass, please let me know.

A fun side effect is that this lets you download Viblo CTF writeups, even though that's forbidden. I reported this to Viblo admin, let's see how long this takes to get fixed, and whether I'd get any bounty.

## Tech stack
Originally this has Redis as database backend, but Heroku's free-tier doesn't let you do that, and I'm poor, so I switched to SQLite. If you want to see the code with Redis, it's the very first commit of this repo.

The progress bar on preparing download is done with SocketIO. The latency is pretty bad, but a good excuse I always use is that I'm not a web developer :)

I tried using Celery for async task, but it was a pain in the ass. So I didn't.

---

Happy birthday to me. Made with love and frustration.