from coincurve import PrivateKey, PublicKey
import hashlib

priv = PrivateKey()
pub = priv.public_key.format().hex()

k1 = "abb10e5d7501bbd1978d008def44b82006a83c74df7b2ec55edc41d6e30d8915"

msg = hashlib.sha256(bytes.fromhex(k1)).digest()
sig = priv.sign(msg).hex()
import requests
r = requests.get(f"http://127.0.0.1:8000/lnurl-auth/lnurl-callback?k1={k1}&key={pub}&sig={sig}")
print(r.json())