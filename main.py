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
    value = None
    file = None

class RequestData:
    action: str
    token: str
    repository: str
    github_username: str
    secret: GithubSecret = GithubSecret()

    def __str__(self):
        return self.secret.name


# Testable
def help(flag=''):
    if flag == 'action':
        print("-a|--action create|update|delete")

    else:
        print("test.py -i <inputfile> -o <outputfile>")


# Testable
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
    """Fetch the current Github user"""
    query_url = f"{github_base_url}/user"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)
    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        request.github_username = namespaced_res.login
        print("Logged in as: " + request.github_username)


def get_secret_encryption_public_key(request: RequestData):
    """Fetch pulic key from Github for secret encryption."""
    query_url = f"{github_base_url}/repos/{request.github_username}/{request.repository}/actions/secrets/public-key"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)
    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        return namespaced_res


def get_secret_names(request: RequestData) -> list:
    """Fetch secret names from Github. Return them as a list."""
    query_url = f"{github_base_url}/repos/{request.github_username}/{request.repository}/actions/secrets"
    headers={'Authorization': f'token {request.token}'}
    res = requests.get(query_url, headers=headers)

    if res.ok:
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())

        return list(map(lambda secret : secret["name"], namespaced_res.secrets))


# Testable
def read_file_contents(request: RequestData):
    try:
        if request.secret.file != None or request.secret.file != "":
            f = open(request.secret.file, encoding = 'utf-8')
            # perform file operations
            return f.read()
    except FileNotFoundError:
        print(f"File not found at specified path: {request.secret.file}")
        sys.exit(1)


# TODO: Move check logic out to make testable
def create_secret(request: RequestData):
    """PUT request to create a repository level secret in Github Actions."""
    if request.secret.value == None and request.secret.file == None:
        print("No secret value or filename provided")
        sys.exit(1)
    elif request.secret.value != None and request.secret.file != None:
        print("Either provide a secret value OR a filename, not both")
        sys.exit(1)
        
    if request.action not in ('update', 'create_or_update'):
        existing_secret_names = get_secret_names(request)
        if request.secret.name in existing_secret_names:
            print(f'<{request.secret.name}> already exists, try action: update|create_or_update')
            sys.exit(1)

    repository_public_key = get_secret_encryption_public_key(request)
    if request.secret.value == None and request.secret.file != None:
        # Read secret value from file
        encrypted_secret = encrypt_secret_value(repository_public_key.key, read_file_contents(request))
    elif request.secret.file == None and request.secret.value != None:
        # Read secret value from command line
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
        print(f"<{request.secret.name}> set successfully!")
        # Converts json to dot notation for easier access on fields
        namespaced_res = SimpleNamespace(**res.json())
        return namespaced_res


    

def update_secret():
    pass


def delete_secret():
    pass


# Testable
def parse_args() -> RequestData:
    """Parse the commannd line input into the request data."""
    try:
        opts, args = getopt.getopt(sys.argv[1:],"a:t:h",
            [
                'action=',
                'token=',
                'help', 
                'secret-name=',
                'secret-value=',
                'repository=',
                'secret-file='
            ])

        request = RequestData()

        # TODO: None checking for mandatory values, maybe a cumulative error printout
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
            elif opt in ('--secret-file'):
                request.secret.file = arg
            elif opt in ('--repository'):
                request.repository = arg

        return request
        # Validate data method

    except getopt.GetoptError as err:
        print(err)
        help()
        sys.exit(2)


def main():
    request = parse_args()

    get_user_details(request)
    make_request_for_action(request)


if __name__ == "__main__":
    main()