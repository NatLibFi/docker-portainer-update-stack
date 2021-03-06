from os import getenv
from re import sub
from http.client import HTTPSConnection as connect
from pathlib import Path
from subprocess import run as run_cmd

from urllib.parse import urlparse
from urllib.parse import urlencode

from json import dumps as json_encode
from json import loads as json_decode

def main():
    check_env()
    stack_names = get_stack_names()
    token = get_auth_token()        
    stacks = find_stacks(token, stack_names) 
    update_stacks(token, stacks)    

def check_env():
    env_list = ['API_URL', 'API_USERNAME', 'API_PASSWORD', 'SWARM_ID', 'COMMIT_SHA_ENV']    
    missing = list(filter(lambda e: getenv(e) == None, env_list))

    if len(missing) > 0:
        raise Exception('Mandatory environment variables missing: {}'.format(missing))    

def get_stack_names():    
    commit_sha_env = getenv('COMMIT_SHA_ENV')
    commit_sha = getenv(commit_sha_env)

    p = run_cmd(['git', 'show', '--name-only', '--oneline'], capture_output=True, text=True)
    
    if p.returncode == 0:        
        # Ditch the first line which contains short sha and message
        file_names = p.stdout.strip().split('\n')[1:]
        iter = filter(lambda f: Path(f).is_file(), file_names)        
        return [*map(lambda f: sub('\.yml$', '', f), iter)]

    raise Exception('Git command failed: {}'.format(p.stderr))

def get_auth_token():
    method = 'POST'
    path = '/auth'
    body = json_encode({ 'Username': getenv('API_USERNAME'), 'Password': getenv('API_PASSWORD')})
    headers = { 'Content-Type': 'application/json' }
    payload = do_request(method='POST', path=path, body=body, headers=headers)

    return payload['jwt']
   
def find_stacks(token, stack_names):
    method = 'GET'
    headers = { 'Authorization': 'Bearer {}'.format(token) }
    filters = json_encode({'SwarmID': getenv('SWARM_ID')})
    path = '/stacks?{}'.format(urlencode({'filters': filters}))
    all_stacks = do_request(method=method, path=path, headers=headers)
    
    return filter(lambda s: s['Name'] in stack_names, all_stacks)

def update_stacks(token, stacks):  
    for stack in stacks:        
        with open('{}.yml'.format(stack['Name'])) as file:
            manifest = file.read()
            method = 'PUT'
            headers = {'Authorization': 'Bearer {}'.format(token), 'Content-Type': 'application/json'}
            path = '/stacks/{}?endpointId={}'.format(stack['Id'], stack['EndpointId'])            
            body = json_encode({**stack, 'Prune': True, 'StackFileContent': manifest})
        
        if getenv('DRY_RUN'):
          print('Not updating stack {} because DRY_RUN is set'.format(stack['Name']))
          return
        
        do_request(method=method, path=path, headers=headers, body=body)            
        print('Updated stack {}'.format(stack['Name']))

def do_request(method='GET', body=None, headers={}, path='/'):
    url = urlparse(getenv('API_URL'))
    abs_path = '{}/api{}'.format(url.path, path)

    debug('{} request to {}:{}{}'.format(method, url.hostname, url.port, abs_path))
    
    connection = connect(url.hostname, url.port)            
    connection.request(method, abs_path, body=body, headers=headers)
    response = connection.getresponse()

    if response.status >= 200 and response.status < 300:
        return json_decode(response.read())

    raise Exception('Unexpected response: {}, {}'.format(response.status, response.read()))

def debug(message):
    if getenv('DEBUG'):
        print('DEBUG: {}'.format(message))

if __name__ == '__main__':
    main()
