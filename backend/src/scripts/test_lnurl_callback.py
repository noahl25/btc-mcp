from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "72fd40463c42eb4a46962840f9573ed54678a28602540f9a9855e40314e9166c"

print(priv.secret.hex())
print(pub)

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://localhost:8000/creator/creator-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())