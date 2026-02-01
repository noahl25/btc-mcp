from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "3c42c46ece6b34589ea6ac1e965ea5d4c612a20fba2af57868fcf492c20ced85"

print(priv.secret.hex())
print(pub)

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://localhost:8000/creator/creator-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())