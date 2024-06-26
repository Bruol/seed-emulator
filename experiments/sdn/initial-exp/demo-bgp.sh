# Delecting existing bridge and data-plane connection with the same name to avoid conflict.
sudo ovs-vsctl del-br br1
sudo ip link del veth-faucet
# sudo ip link del veth-faucet-ovs

# Creating a SDN bridge with name "br1"
# Settting controller to the SDN bridge
# Setting the fail_mode:secure, so that this behaves like a proper SDB bridge
# Controller is a separate program named faucet running on localhost:6653
# Setting a datapath id 1 for the controller
# Setting disable in-band-connection so that each bridge (switch) is connected to the controller directly.

sudo ovs-vsctl add-br br1 \
-- set bridge br1 other-config:datapath-id=0000000000000001 \
-- set bridge br1 other-config:disable-in-band=true \
-- set bridge br1 fail_mode=secure \
-- set-controller br1 tcp:127.0.0.1:6653

# Already created 4 docker containers (host-a1, host-a2, host-b1, host-b2) with docker-compose.yml file

# Attaching each container to a port of the bridge and setting up a port inside the docker container with the name eth0
sudo ovs-docker add-port br1 eth0 host-a1 --ipaddress=10.150.1.1/24 --gateway=10.150.1.252 
sudo ovs-docker add-port br1 eth0 host-a2 --ipaddress=10.150.1.2/24 --gateway=10.150.1.252
sudo ovs-docker add-port br1 eth0 host-b1 --ipaddress=10.150.2.1/24 --gateway=10.150.2.252
sudo ovs-docker add-port br1 eth0 host-b2 --ipaddress=10.150.2.2/24 --gateway=10.150.2.252
#sudo ovs-docker add-port br1 sdn0 host-c1 --ipaddress=10.150.3.1/24 --gateway=10.150.3.254
#sudo ovs-docker add-port br1 sdn0 host-c2 --ipaddress=10.150.3.2/24 --gateway=10.150.3.254

# Adding data plane connection to the switch
# It basically creating a network device in the lan
# so that bgp router can peer with the router in the controller.
sudo ip link add veth-faucet type veth peer name veth-faucet-ovs
sudo ovs-vsctl add-port br1 veth-faucet-ovs
sudo ip addr add 10.150.1.253/24 dev veth-faucet
sudo ip link set veth-faucet up
sudo ip link set veth-faucet-ovs up

# Adding a BGP router to the LAN, this BGP router is created using mini-internet of seed-emulator.
# Hence before running this scrpit, user need to start all the containers.
# Containers from both the emulator's docker compose and also from the manually created docker-compose file for small SDN network.  
# This command is basically attaching the BGP-router (generated by seed-emulator) to the sdn bridge
# and it will also create a new network interface in the router with the name sdn0.
# That sdn0 interface is connected to the openvswitch bridge.

sudo ovs-docker add-port br1 sdn0 as150r-router0-10.150.0.254 --ipaddress=10.150.1.254/24

# faucet-bgp.yaml is the configuration for the SDN controller. 
# These two lines are basically setting the controller and restart the controller to load the new configuration.
sudo cp faucet-bgp.yaml /etc/faucet/faucet.yaml
sudo systemctl restart faucet
