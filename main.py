import sys, getopt
import requests
from types import SimpleNamespace
import json
from base64 import b64encode
from nacl import encoding, public

# ACTION: Create/Update/Delete [STRING]
# TOKEN: GITHUB ACCESS TOKEN [STRING]
# SECRET NAME: [STRING]
# SECRET VALUE: [STRING, INT?]

github_base_url = "https://api.github.com"

class GithubSecret:
    name: str
    value: str


class RequestData:
    action: str
    token: str
    repository: str
    github_username: str
    secret: GithubSecret = GithubSecret()

    def __str__(self):
        return self.secret.name


def help(flag=''):
    if flag == 'action':
        print("-a|--action create|update|delete")
    print("test.py -i <inputfile> -o <outputfile>")


def make_request_for_action(request: RequestData):
    if request.action == "create":
        return create_secret(request)
    elif request.action == "update":
        update_secret()
    elif request.action == "delete":
        delete_secret()
    else:
        help('action')


def encrypt_secret_value(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def get_user_details(request: RequestData):
    """Get the Github user"""
    query_url = f"{github_base_url}/user"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)
    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        request.github_username = namespaced_res.login
        print("Logged in as: " + request.github_username)


def get_secret_encryption_public_key(request: RequestData):
    """Get pulic key from Github for secret encryption"""
    query_url = f"{github_base_url}/repos/{request.github_username}/{request.repository}/actions/secrets/public-key"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)
    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        return namespaced_res


def get_secret_names(request: RequestData):
    query_url = f"{github_base_url}/repos/{request.github_username}/{request.repository}/actions/secrets"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)

    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())

        return list(map(lambda secret : secret["name"], namespaced_res.secrets))


def create_secret(request: RequestData):
    existing_secret_names = get_secret_names(request)
    if request.secret.name in existing_secret_names:
        print(f'<{request.secret.name}> already exists, try action: update|create_or_update')
        exit

    repository_public_key = get_secret_encryption_public_key(request)
    encrypted_secret = encrypt_secret_value(repository_public_key.key, request.secret.value)
    
    query_url = f"{github_base_url}/repos/{request.github_username}/{request.repository}/actions/secrets/{request.secret.name}"
    headers = {
        'Authorization': f'token {request.token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'encrypted_value': f'{encrypted_secret}', 
        'key_id': f'{repository_public_key.key_id}'
    }
    res = requests.put(query_url, headers=headers, data=json.dumps(data))
    
    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        return namespaced_res


    

def update_secret():
    pass


def delete_secret():
    pass


def parse_args() -> RequestData:
    try:
        opts, args = getopt.getopt(sys.argv[1:],"a:t:h",
            [
                'action=',
                'token=',
                'help', 
                'secret-name=',
                'secret-value=',
                'repository='
            ])

        request = RequestData()

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                help()
                sys.exit()

            elif opt in ('-a', '--action'):
                request.action = arg
            elif opt in ('-t', '--token'):
                request.token = arg
            elif opt in ('--secret-name'):
                request.secret.name = arg
            elif opt in ('--secret-value'):
                request.secret.value = arg
            elif opt in ('--repository'):
                request.repository = arg

        return request

    except getopt.GetoptError:
      help()
      sys.exit(2)


def get_name(secret):
    return secret["name"]

def main():
    request = parse_args()

    get_user_details(request)
    response = make_request_for_action(request)
    get_secret_encryption_public_key(request)
    # existing_secret_names = list(map(lambda secret : secret["name"], response["secrets"]))

    print("Secret to set: <" + request.secret.name + ">")


if __name__ == "__main__":
    main()