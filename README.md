An improved python version based on the original bash version, written by @connorw600 

This script is designed to keep a list of all participating open nodes in memory as well as perform GeoIP lookups on 
each open node and push the open nodes to DNS records.
The script re-scans existing nodes every 5 minutes as well as fetch new nodes from the monerod peer list.


####Dependencies
* libgeoip-dev (ubuntu)
* libgeoip-devel (centos)
* [pdns-server](https://repo.powerdns.com/)
* GeoIP.dat ([GeoIP  County Lite](https://dev.maxmind.com/geoip/legacy/install/country/)) 

#### Licence
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