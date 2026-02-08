import lightspark
from lightspark import TransactionStatus
import bolt11
import time
import httpx

class LightsparkClient:

    def __init__(self, lightspark_client_id: str, lightspark_client_secret: str, lightspark_node_id: str, lightspark_node_password: str, max_spend: int | None):
        self.max_spend = max_spend
        self.client = lightspark.LightsparkSyncClient(
            api_token_client_id=lightspark_client_id,
            api_token_client_secret=lightspark_client_secret,
        )
        signing_key = self.client.recover_node_signing_key(lightspark_node_id, lightspark_node_password)
        self.client.load_node_signing_key(lightspark_node_id, signing_key)
        self.node_id = lightspark_node_id
        
    def set_max_spend(self, max_spend: int):
        self.max_spend = max_spend

    def pay_invoice(self, invoice: str):
        decoded = bolt11.decode(invoice)
        sats: int = decoded.amount_msat // 1000 #type: ignore
        usd: float = float(httpx.get(f"http://localhost:8000/api/payments/sats-to-usd/{sats}").text)
        if self.max_spend and usd > self.max_spend:
            return { "status": "failed", "message": "Payment would exceed spending budget." }
        outgoing = self.client.pay_invoice(node_id=self.node_id, encoded_invoice=invoice, timeout_secs=60, maximum_fees_msats=1000)  # type: ignore
        for _ in range(30):
            if outgoing.status not in (TransactionStatus.PENDING, TransactionStatus.NOT_STARTED):  # type: ignore
                break
            time.sleep(2)
            outgoing = self.client.get_entity(outgoing.id, lightspark.OutgoingPayment)  # type: ignore
        if outgoing.status == TransactionStatus.SUCCESS:  # type: ignore
            if self.max_spend:
                self.max_spend -= usd
            try:
                httpx.post("http://localhost:8000/api/payments/set-as-paid", params={"id": invoice})
            except Exception:
                pass
            return { "status": "success" }
        return { "status": "failed", "message": f"Payment failed. Status: {outgoing.status}, Reason: {outgoing.failure_reason}, Details: {outgoing.failure_message}" }  # type: ignore