```text
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                   Version 2, December 2004

Copyright (C) 2017 Connorw600 <connorw600@lchi.mp>

Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.

           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
  TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

 0. You just DO WHAT THE FUCK YOU WANT TO.
 ```

And improved scanner written in python based on the original by [connorw600](https://www.viaxmr.com/) 

This script is designed to keep a list of all participating open nodes in memory as well as perform GeoIP lookups on 
each open node and push the open nodes to DNS records.
The script re-scans existing nodes every 15 minutes as well as fetch new nodes from the monerod peer list.


* Port 18081 nodes are available by using ``nodes.viaxmr.com``
* Port 18089 nodes are available by using ``mwnodes.viaxmr.com``


### Dependencies
* [pdns-server](https://repo.powerdns.com/)
* [GeoIP2  County Lite](http://dev.maxmind.com/geoip/geoip2/geolite2/)
* python [requests](https://pypi.python.org/pypi/requests/)
* python [geoip2](https://pypi.python.org/pypi/geoip2/)