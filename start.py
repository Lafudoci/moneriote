from subprocess import Popen
from threading import Thread
from time import sleep

import json
import re
import GeoIP  # Bad news if you're running this on windows without devel packages
import requests
import subprocess

monerodLocation = '../bin/monerod'  # This is the relative or full path to the monerod binary
moneroDaemonAddr = '127.0.0.1'  # The IP address that the rpc server is listening on
moneroDaemonPort = '18081'  # The port address that the rpc server is listening on
moneroDaemonAuth = 'not:used'  # The username:password that the rpc server requires (if set) - has to be something

acceptableBlockOffset = 2  # How much variance in the block height will be allowed
scanInterval = 5  # 5 Minutes
rpcPort = 18089  # This is the rpc server port that we'll check for

dnsApiZone = 'nodes.viaxmr.com.'  # the dns zone that we'll use
dnsApiEnd = 'http://ns1.lchimp.com:8081/api/v1/servers/localhost/zones/'  # the zone's end point on the api server
dnsApiKey = ''  # this is your powerdns API key set in the server config

gi = GeoIP.open('./GeoIP.dat', GeoIP.GEOIP_MEMORY_CACHE)
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


def scan_node(address, accepted_height):
    try:
        req = requests.get('http://' + address + ':' + rpcPort.__str__() + '/getheight', timeout=5)
    except:
        return

    try:
        node_height_json = json.loads(req.text)
    except:
        return

    block_height_diff = int(node_height_json['height']) - accepted_height

    # Check if the node we're checking is up to date (with a little buffer)
    if block_height_diff >= acceptableBlockOffset or block_height_diff <= (
                acceptableBlockOffset * -1) and address in currentNodes:
        currentNodes.remove(address)
    elif address not in currentNodes:
        currentNodes.append(address)


"""
    Start threads looking for new nodes
"""


def check_for_new_nodes():
    new_nodes = load_nodes()
    block_height = get_blockchain_height()
    threads = [Thread(target=scan_node, args=(node, block_height)) for node in new_nodes]

    # TODO: Don't hammer the CPU and network, make this so only 15-20 scans happen at once
    for x in threads:
        x.start()

    for x in threads:
        x.join()


"""
    Start threads checking our existing known nodes to see if they're still alive
"""


def check_existing_nodes():
    blockchain_height = get_blockchain_height()
    threads = [Thread(target=scan_node, args=(node, blockchain_height)) for node in currentNodes]

    # TODO: Don't hammer the CPU and network, make this so only 15-20 scans happen at once
    for x in threads:
        x.start()
    for x in threads:
        x.join()


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
        county_code = gi.country_code_by_addr(node)
        region_code = GeoIP.country_continents[county_code]
        dns_nodes.append({"content": node, "disabled": False})
        dns_geo_nodes[region_code].append({"content": node, "disabled": False})

    jsonData = {
        "rrsets": [
            {
                "name": "nodes.viaxmr.com.",
                "type": "A",
                "ttl": 60,
                "changetype": "REPLACE",
                "records": dns_nodes
            }
        ]
    }

    for region, nodes in dns_geo_nodes.iteritems():
        jsonData["rrsets"].append(
            {
                "name": region + ".nodes.viaxmr.com.",
                "type": "A",
                "ttl": 60,
                "changetype": "REPLACE",
                "records": nodes
            })

    requests.patch(dnsApiEnd + dnsApiZone, json.dumps(jsonData), headers={'X-API-Key': dnsApiKey}, timeout=3)


def check_all_nodes():
    print ('Checking existing nodes')
    check_existing_nodes()
    print ('Checking for new nodes')
    check_for_new_nodes()
    print ('Building DNS records')
    update_dns_records()

    print ("We currently have {} nodes".format(currentNodes.__len__()))


while True:
    check_all_nodes()
    sleep(scanInterval * 60)
