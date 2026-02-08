from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "11e3a169c4f775af5d32976d74e29246f11ff406f16706340efbc3a324a75532"

print(priv.secret.hex())
print(pub)

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://localhost:8000/creator/creator-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())