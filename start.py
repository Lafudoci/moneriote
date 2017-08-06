from functools import partial
from multiprocessing import Pool, freeze_support
from subprocess import Popen
from time import sleep

import json
import re
import geoip2.database
import requests
import subprocess

monerodLocation = '../bin/monerod'  # This is the relative or full path to the monerod binary
moneroDaemonAddr = '127.0.0.1'  # The IP address that the rpc server is listening on
moneroDaemonPort = '18081'  # The port address that the rpc server is listening on
moneroDaemonAuth = 'not:used'  # The username:password that the rpc server requires (if set) - has to be something

maximumConcurrentScans = 16  # How many servers we should scan at once
acceptableBlockOffset = 3  # How much variance in the block height will be allowed
scanInterval = 15  # 15 Minutes
rpcPort = 18081  # This is the rpc server port that we'll check for

dnsApiZone = 'nodes.viaxmr.com.'  # the dns zone that we'll use
dnsApiEnd = 'http://ns1.lchimp.com:8081/api/v1/servers/localhost/zones/'  # the zone's end point on the api server
dnsApiKey = ''  # this is your powerdns API key set in the server config

gi = geoip2.database.Reader('./GeoLite2-Country.mmdb')
currentNodes = []

'''
    Gets the current top block on the chain
'''


def get_blockchain_height():
    process = Popen([
        monerodLocation,
        '--rpc-bind-ip', moneroDaemonAddr,
        '--rpc-bind-port', moneroDaemonPort,
        '--rpc-login', moneroDaemonAuth,
        'print_height'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1)
    (output, err) = process.communicate()
    return int(re.sub('[^0-9]', '', output.splitlines()[1]))


'''
    Gets the last known peers from the server
'''


def load_nodes():
    nodes = []
    process = Popen([
        monerodLocation,
        '--rpc-bind-ip', moneroDaemonAddr,
        '--rpc-bind-port', moneroDaemonPort,
        '--rpc-login', moneroDaemonAuth,
        'print_pl'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1)

    (output, err) = process.communicate()

    regex = r"(gray|white)\s+(\w+)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})"
    matches = re.finditer(regex, output)

    for matchNum, match in enumerate(matches):
        if match.group(1) == 'white':
            address = match.group(3)

            if address not in currentNodes:
                nodes.append(address)

    return nodes


"""
    Scans the requested address to see if the RPC port is available and is within the accepted range
"""


def scan_node(accepted_height, address):
    try:
        req = requests.get('http://' + address + ':' + rpcPort.__str__() + '/getheight', timeout=5)
    except requests.exceptions.RequestException:
        if address in currentNodes:
            currentNodes.remove(address)
        return

    try:
        node_height_json = json.loads(req.text)
    except:
        if address in currentNodes:
            currentNodes.remove(address)
        return

    block_height_diff = int(node_height_json['height']) - accepted_height

    # Check if the node we're checking is up to date (with a little buffer)
    if (block_height_diff >= acceptableBlockOffset or block_height_diff <= (acceptableBlockOffset * -1)) \
            and address in currentNodes:
        currentNodes.remove(address)
    elif address not in currentNodes:
        currentNodes.append(address)


"""
    Start threads checking known nodes to see if they're alive
"""


def start_scanning_threads(current_nodes, blockchain_height):
    pool = Pool(processes=maximumConcurrentScans)
    pool.map(partial(scan_node, blockchain_height), current_nodes)
    pool.close()
    pool.join()


"""
    Start threads looking for new nodes
"""


def check_for_new_nodes():
    new_nodes = load_nodes()

    for node in new_nodes:
        if node in currentNodes:
            new_nodes.pop(node)

    start_scanning_threads(new_nodes, get_blockchain_height())


"""
    Update our powerdns authorative records
"""


def update_dns_records():
    dns_geo_nodes = {
        '--': [],
        'AF': [],
        'AN': [],
        'AS': [],
        'EU': [],
        'NA': [],
        'OC': [],
        'SA': []
    }
    dns_nodes = []

    for node in currentNodes:
        geo_lookup = gi.country(node)
        dns_nodes.append({"content": node, "disabled": False})
        dns_geo_nodes[geo_lookup.continent.code].append({"content": node, "disabled": False})

    json_data = {
        "rrsets": [
            {
                "name": dnsApiZone,
                "type": "A",
                "ttl": 60,
                "changetype": "REPLACE",
                "records": dns_nodes
            }
        ]
    }

    for region, nodes in dns_geo_nodes.iteritems():
        json_data["rrsets"].append(
            {
                "name": "{}.{}".format(region, dnsApiZone),
                "type": "A",
                "ttl": 60,
                "changetype": "REPLACE",
                "records": nodes
            })

    requests.patch(dnsApiEnd + dnsApiZone, json.dumps(json_data), headers={'X-API-Key': dnsApiKey}, timeout=3)


def check_all_nodes():
    print ('Checking existing nodes')
    start_scanning_threads(currentNodes, get_blockchain_height())
    print ('Checking for new nodes')
    check_for_new_nodes()
    print ('Building DNS records')
    update_dns_records()

    print ("We currently have {} nodes".format(currentNodes.__len__()))


if __name__ == '__main__':
    freeze_support()

    while True:
        check_all_nodes()
        sleep(scanInterval * 60)
