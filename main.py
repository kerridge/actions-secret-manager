import sys, getopt
import requests

# ACTION: Create/Update/Delete [STRING]
# TOKEN: GITHUB ACCESS TOKEN [STRING]
# SECRET NAME: [STRING]
# SECRET VALUE: [STRING, INT?]

class GithubActionsInput:
    action = ''
    token = ''
    secret_name = ''
    secret_value = ''

    def __str__(self):
        return self.secret_name


def help(flag):
    if flag == 'action':
        print("-a|--action create|update|delete")
    print("test.py -i <inputfile> -o <outputfile>")


def make_request_for_action(user_input: GithubActionsInput):
    if user_input.action == "create":
        return add_secret(user_input)
    elif user_input.action == "update":
        update_secret()
    elif user_input.action == "delete":
        delete_secret()
    else:
        help('action')


def encrypt_secret_value() -> str:
    print("ENCRYPT")
    return ''


def get_secret_encryption_public_key():
    pass


def add_secret(user_input: GithubActionsInput):
    owner = "kerridge"
    repo = "django-s3-stack"
    query_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets"
    headers={'Authorization': f'token {user_input.token}'}
    return requests.get(query_url, headers=headers)


def update_secret():
    pass


def delete_secret():
    pass


def parse_args():
    try:
        opts, args = getopt.getopt(sys.argv[1:],"a:t:h",
            [
                'action=',
                'token=',
                'help', 
                'secret-name=',
                'secret-value='
            ])

        user_input = GithubActionsInput()

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                help()
                sys.exit()

            elif opt in ('-a', '--action'):
                user_input.action = arg
            elif opt in ('-t', '--token'):
                user_input.token = arg
            elif opt in ('--secret-name'):
                user_input.secret_name = arg
            elif opt in ('--secret-value'):
                user_input.secret_value = arg

        return user_input

    except getopt.GetoptError:
      help()
      sys.exit(2)


def get_name(secret):
    return secret["name"]

def main():
    user_input = parse_args()
    response = make_request_for_action(user_input).json()

    existing_secret_names = list(map(lambda secret : secret["name"], response["secrets"]))

    print("Secret to set: <" + user_input.secret_name + ">")


if __name__ == "__main__":
    main()