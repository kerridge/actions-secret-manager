import sys, getopt, textwrap
from github.Repository import Repository
import requests
from types import SimpleNamespace
import json
from base64 import b64encode
from nacl import encoding, public
from typing import Final

from github import Github, BadCredentialsException
from github.GithubException import UnknownObjectException

# ACTION: Create/Update/Delete [STRING]
# TOKEN: GITHUB ACCESS TOKEN [STRING]
# SECRET NAME: [STRING]
# SECRET VALUE: [STRING, INT?]

github_base_url = "https://api.github.com"

class ValidActions:
    CREATE: Final = 'create'
    UPDATE: Final = 'update'
    DELETE: Final = 'delete'

    ALL_ACTIONS: Final = (CREATE, UPDATE, DELETE)
    CREATE_ACTIONS: Final = (CREATE, UPDATE)


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
    if request.action == ValidActions.CREATE:
        return create_secret(request)
    elif request.action == ValidActions.UPDATE:
        update_secret()
    elif request.action == ValidActions.DELETE:
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


def get_github_client(request: RequestData, message) -> Github:
    try:
        g = Github(request.token)
        print(f"Logged in as {g.get_user().login}")
        return g
    except BadCredentialsException:
        raise ValueError(message)


def get_github_repository(request: RequestData, g: Github):
    repo = g.get_repo(request.repository)
    return repo


def create_github_repository_secret(request: RequestData, repo: Repository):
    res = repo.create_secret(request.secret.name, request.secret.value)
    return res

def format_private_key(request: RequestData):
    begin_ssh_line="-----BEGIN OPENSSH PRIVATE KEY-----"
    end_ssh_line="-----END OPENSSH PRIVATE KEY-----"

    if begin_ssh_line in request.secret.value:
        temp_secret: str = request.secret.value
        temp_secret = temp_secret.replace((begin_ssh_line+' '), (begin_ssh_line+'\n'))
        temp_secret = temp_secret.replace((' '+end_ssh_line), ('\n'+end_ssh_line))
        temp_secret = textwrap.fill(temp_secret, 70)

        print("FORMATTED: ", temp_secret)
        return temp_secret


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
        # TODO: Fix null checking
        if request.secret.file != '':
            f = open(request.secret.file, encoding = 'utf-8')
            # perform file operations
            return f.read()
    except FileNotFoundError:
        print(f"File not found at specified path: {request.secret.file}")
        sys.exit(1)


# TODO: Move check logic out to make testable
def create_secret(request: RequestData):
    """PUT request to create a repository level secret in Github Actions."""
    if request.action not in ('update', 'create_or_update'):
        existing_secret_names = get_secret_names(request)
        if request.secret.name in existing_secret_names:
            print(f'<{request.secret.name}> already exists, try action: update|create_or_update')
            sys.exit(1)

    repository_public_key = get_secret_encryption_public_key(request)
    if request.secret.file == None and request.secret.value != None:
        # Read secret value from command line
        print("============================")
        print("VALUE: ", request.secret.value)
        print("============================")
        encrypted_secret = encrypt_secret_value(repository_public_key.key, request.secret.value)
        print("SECRET: ", encrypted_secret)
    
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


def validate_request(request: RequestData):
    errors = list()

    if request.action not in ValidActions.ALL_ACTIONS:
        help('action')
        errors.append(f"`{request.action}` is not in available actions {ValidActions.ALL_ACTIONS}")

    if request.action in ValidActions.CREATE_ACTIONS:
        # No value or file provided
        if request.secret.file == None and request.secret.value == None:
            errors.append("Provide either a file or a value")
        # Value AND file provided
        elif request.secret.file != None and request.secret.value != None:
            errors.append("Provide either a file or a value, not both")

    if errors.__len__() > 0:
        for error in errors:
            print(error)
        sys.exit(1)


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
            if arg == '':
                arg = None

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
                # Automatically added to env by github. Follows {user}/{reposiitory}
                request.repository = arg
                # request.repository = arg.split('/')[1]

        validate_request(request)
        return request

    except getopt.GetoptError as err:
        print(err)
        help()
        sys.exit(2)


def main():
    request = parse_args()

    request.secret.value = format_private_key(request)

    g = get_github_client(request, "Couldn't get user bruh")
    repo = get_github_repository(request, g)
    secret_added = create_github_repository_secret(request, repo)

    # TODO: move to somewhere
    if secret_added:
        print(f"<{request.secret.name}> added to repository!")
    else:
        print(f"<{request.secret.name}> couldn't be added")
        

    # get_user_details(request)
    # # TODO: Get existing secrets?
    # make_request_for_action(request)


if __name__ == "__main__":
    main()