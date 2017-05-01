# Nuvo Polyglot

 This node server supports the Nuvo Audio Controller connected via a GlobalCache deivce. The Global Cache client is gc_client.py and you could easily substitute a new client. The client just needs a method client.msg to receive the serial command to be sent to the Global Cache device.

## Prepare package

 * `git clone <repo> && cd <repo>`
 * Edit the config.yaml file and overwrite and zone names that you would like to customize
 * Edit the profile/nls/en_us.txt file and overwrite custom group names and source names
 * Zip profile, remove profile.zip in root if it exists and then `cd profile`  `zip -r profile.zip *`  `mv profile.zip ..`


## Deployment
 
### Raspberry Pi
 * ssh into rpi
 * `mkdir -p ~/config/node_servers/nuvo-polyglot`
 * Move the prepared package into the created directory `cp *.{py,yaml,zip,txt} ~/config/node_servers/nuvo-polyglot/`
 * `docker build -t <tag> .`  ex. `docker build -t brettahale/polyglot`
 * `docker run --name polyglot -v /home/pi/config:/home/polyglot/Polyglot/config:rw -p 8080:8080 <tag>`

### Node Server
 * Navigte to node server rpi.ip.address:8080
 * Add Node Server Choosing Nuvo as the type, Any Name, and Node Server ID should be an open slot in the ISY that you plan to use (1-10)
 * Click on the running server in the left navigation
 * Download profile.zip by clicking the download button above the server name
 * Make note of this line under the Node server name `Node Server: <num> | Base URL: /ns/<key>`

### ISY
 * In the ISY Administrative Console open the "Node Servers > Configure" menu and choose the slot where you added the new Node Server
 * Add any profile name
 * User ID and Password for your Node Server (Default: admin/admin)
 * Add the Base URL from the Node Server
 * Change the port to 8080
 * Click Upload Profile and choose the profile.zip the you downloaded
 * Click OK
 * Reboot ISY
 * Using the same process, upload the same profile.zip again and reboot. -- Current Quirk for this process

