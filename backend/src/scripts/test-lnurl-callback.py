from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "82d5fc9d9a1569a563273817438832a18efab86c9accd27bf6a63fb880221048"

print(str(priv))
print(pub)

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://localhost:8000/creator/creator-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())