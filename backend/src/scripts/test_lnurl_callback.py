from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "b69326a0f6fbdbc6d38da315a3934c1580d2f12260b02ae73ed78ac808b94577"

print(priv.secret.hex())
print(pub)

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://localhost:8000/creator/creator-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())