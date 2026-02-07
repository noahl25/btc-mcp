import lightspark
import os
from dotenv import load_dotenv
import bolt11

load_dotenv()

invoice = "lnbcrt1p5cvw7fpp5lz9e23y8k65mfjvqtpzruzq3lyxpq9lwuglulsy2lfvw6f6hqrvqdqqcqzpgxqyz5vqrzjqgp0s738klwqef7yr8yu54vv3wfuk4psv46x5laf6l6v5x4lwwahvqqqqqjp6chwtgqqqqqqqqqqqqqq9qsp5q8y2gwdt3whffkfx3updd09wykans2a837stu5w5zy5na7hrxz7q9qxpqysgq4wpt80mknjmet70cnfmhwdws4z8udw64pxwgkrgpvawsvzjc62ghjee4x99mtk5zvlcegkk69dnad9vcw6wultm70g6ahte5kqfyf6gqm5rgm9"

def main():
        
    # ls_client_id = os.getenv("LIGHTSPARK_ID")
    # ls_secret = os.getenv("LIGHTSPARK_SECRET")
    # ls_node_id = os.getenv("LIGHTSPARK_NODE")

    # if not ls_client_id or not ls_secret or not ls_node_id:
    #     return
    
    # client = lightspark.LightsparkSyncClient(
    #     api_token_client_id=ls_client_id,
    #     api_token_client_secret=ls_secret,
    # )

    print(bolt11.decode(invoice))


main()