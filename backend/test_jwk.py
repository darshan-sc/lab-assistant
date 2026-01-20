from jose import jwk
import json

jwks_json = """{"keys":[{"alg":"ES256","crv":"P-256","ext":true,"key_ops":["verify"],"kid":"c5d54f04-5e65-4450-bc00-ee01df68e965","kty":"EC","use":"sig","x":"SjadDTQXaxtaNJVkTDrILKSAByQeRwtpYBiy6boV5Z4","y":"bhBvthfcaeNEAZa_uZrKnZoFpzNEpP7mx2JhikgrBbM"}]}"""
jwks = json.loads(jwks_json)
key_data = jwks["keys"][0]

try:
    key = jwk.construct(key_data)
    print(f"Successfully constructed key: {key}")
    print(f"Public Key PEM: {key.to_pem().decode('utf-8')}")
except Exception as e:
    print(f"Error constructing key: {e}")
