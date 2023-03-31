import os

from dotenv import load_dotenv

load_dotenv()


def get_stripe_keys(request):
    return {"PUBLIC": os.getenv("STRIPE_LIVE_PUBLIC_KEY"), "TEST": "1234"}
