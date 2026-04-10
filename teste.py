import jwt
import requests
from jwt.algorithms import RSAAlgorithm

def validate_microsoft_token(token: str, expected_audience: str):
    # 1️⃣ Extrai o payload sem verificar a assinatura
    unverified_payload = jwt.decode(token, options={"verify_signature": False})
    unverified_header = jwt.get_unverified_header(token)

    iss = unverified_payload.get("iss")
    kid = unverified_header.get("kid")

    if not iss:
        raise ValueError("❌ Token não contém o campo 'iss'")

    # 2️⃣ Determina automaticamente se é v1 ou v2
    if "sts.windows.net" in iss:
        version = "v1"
        tenant_id = iss.strip("/").split("/")[-1]
        jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/keys"
    elif "login.microsoftonline.com" in iss and "/v2.0" in iss:
        version = "v2"
        tenant_id = iss.split("/")[3]
        jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    else:
        raise ValueError(f"❌ Emissor desconhecido: {iss}")

    print(f"🧭 Detected {version.upper()} token for tenant {tenant_id}")

    # 3️⃣ Baixa as chaves públicas corretas
    jwks = requests.get(jwks_uri).json()
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key:
        raise ValueError("❌ Nenhuma chave pública correspondente encontrada (kid não bate)")

    # 4️⃣ Cria a chave pública RSA
    public_key = RSAAlgorithm.from_jwk(key)

    # 5️⃣ Valida o token
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=expected_audience,
        issuer=iss,
    )

    print("✅ Token válido!")
    return decoded


# ====== USO ======

token = "eyJ0eXAiOiJKV1QiLCJub25jZSI6IjJjUV9vREJJeHBwaGZxXzR6Wm9fSGktQnVabGFveFRUQl9RNnNkWkVUR3MiLCJhbGciOiJSUzI1NiIsIng1dCI6InlFVXdtWFdMMTA3Q2MtN1FaMldTYmVPYjNzUSIsImtpZCI6InlFVXdtWFdMMTA3Q2MtN1FaMldTYmVPYjNzUSJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81ZjlkNzRjOC1lYzkyLTQ0ODgtYTJjNy1iZGNlNjM0MjYyZmEvIiwiaWF0IjoxNzYyMTc3NDUwLCJuYmYiOjE3NjIxNzc0NTAsImV4cCI6MTc2MjE4MjM0MSwiYWNjdCI6MCwiYWNyIjoiMSIsImFjcnMiOlsicDEiXSwiYWlvIjoiQVpRQWEvOGFBQUFBMmxUbEdMUVFTSU12RmRBRjFkK21aOTNoUE5zOWNDbHJQb3RIdGpYTVFqTnBiNkdCbWIybmE5ZXFQVllBZnNCeG1iM01janhYajRKaUFxUW1UbnFpWXR3MXVhOUlvbVRqcWxCRVRudHlaS0RhT0JJWXFLeVpHL1ZlbForYWZHSEdaQW9JZnRMbkc4aTUyNmFTSXpGd0NrRjNqSk1ZdGR4OE0wTDRQY09oWmZheVdQUy94c2NDZ29BbjBOWDl1UHBDIiwiYW1yIjpbInB3ZCIsIm1mYSJdLCJhcHBfZGlzcGxheW5hbWUiOiJ0ZXN0ZSBzYWxlc2ZvcmNlIiwiYXBwaWQiOiI2ZWU5ZDI3Mi1lYWU4LTQxMDktYTRlOC01NGQyODlhNjk0OGEiLCJhcHBpZGFjciI6IjEiLCJmYW1pbHlfbmFtZSI6IkFyYXVqbyIsImdpdmVuX25hbWUiOiJCcnVubyIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjIwMS43NS4xODYuMTAwIiwibmFtZSI6IkJydW5vIEFuaWNldG8gZGUgQXJhdWpvIiwib2lkIjoiZTk5NTI4ZDQtODljMi00NGYyLWFhYTQtMDRiZGMyNjRhZGQzIiwib25wcmVtX3NpZCI6IlMtMS01LTIxLTE2Njc2ODgxMjUtMjQ1MTU0NjE3LTQyODc5MTUyNTQtMTM1MTgwIiwicGxhdGYiOiI1IiwicHVpZCI6IjEwMDMyMDA1MjQzQzQ1QTgiLCJyaCI6IjEuQVNVQXlIU2RYNUxzaUVTaXg3M09ZMEppLWdNQUFBQUFBQUFBd0FBQUFBQUFBQUR0QU4wbEFBLiIsInNjcCI6IlVzZXIuUmVhZCBwcm9maWxlIG9wZW5pZCBlbWFpbCIsInNpZCI6IjAwYTg1NWQ5LTVjNmMtMTJjNC1jYTViLTc5NGY0MzA4ZDc4YyIsInNpZ25pbl9zdGF0ZSI6WyJrbXNpIl0sInN1YiI6IksySHA2dVZLakxwdXh4eUp5QmRKc1pBUGtJVGUzeDdCZU5ZaUF4WlEyOTgiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiU0EiLCJ0aWQiOiI1ZjlkNzRjOC1lYzkyLTQ0ODgtYTJjNy1iZGNlNjM0MjYyZmEiLCJ1bmlxdWVfbmFtZSI6ImJhcmF1am8uc2FsZXNmb0BzYWJlc3AuY29tLmJyIiwidXBuIjoiYmFyYXVqby5zYWxlc2ZvQHNhYmVzcC5jb20uYnIiLCJ1dGkiOiJSOGRSNnlzUmprV29tX2xFbEotM0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2FjZCI6MTc2MTgzNzMxNCwieG1zX2FjdF9mY3QiOiI5IDMiLCJ4bXNfZnRkIjoiUlFuSGRuSXdZNmpfNnhzT1dHY0M3NTl0UXExR1p3MGdleTNsbkYtNkZIc0JkWE56YjNWMGFDMWtjMjF6IiwieG1zX2lkcmVsIjoiMSAxMiIsInhtc19zdCI6eyJzdWIiOiJDdU5tSzh3XzJpNFpsMnZqT2RLNWhXd2lXQXpaSXFSbTlGbUY0UUMzTy0wIn0sInhtc19zdWJfZmN0IjoiMyAxMiIsInhtc190Y2R0IjoxNDk5MTkwOTg3LCJ4bXNfdG50X2ZjdCI6IjYgMyJ9.W1e8N1YShB3qhLQjPACysWOeejMTC9DGc49Imtk9aCizjc7E7bH5X6_vGogx-QSYMFwdgDuHlugZMJB6qoIwTwV0_CbvBuGq2Kg7sNOnw5p_0c2YjGpZKOSQHIRkiMd9mW8Pe7bsZfMl0aKPBMx1UDoCiUyDxfEQxz57Nu_ZuxK9jbx6XNVVEeds8MhwU3M3xWrvIwoWrusbFIssnEgPR5WMfHdegldBaq1KNjlLH1-On4qQwnVlbpRucsGyY2MjLa388DcdNLOBt1oq0tF76d7WK1XaNYEPcLC6OmaTM67hVgEtpekELJHTaCZoYJ2lBFf5EJ4HkuIK06jOlCpkTw"
expected_audience = "00000003-0000-0000-c000-000000000000"  # Ou o 'aud' exato do token

claims = validate_microsoft_token(token, expected_audience)
print("\n📜 Claims decodificados:")
for k, v in claims.items():
    print(f"  {k}: {v}")




