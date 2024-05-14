import os
import docker
from tqdm import tqdm
import time





class TestFunction:
    f = None
    name: str
    args = []
    kwargs = {}

    def __init__(self, func, name, *args, **kwargs):
        self.f = func
        self.name = name
        self.args = args
        self.kwargs = kwargs
    
    def __call__(self, *args, **kwargs):
        return self.f(*args, *self.args, **kwargs, **self.kwargs)
    
    def __str__(self):
        return self.name 




client = docker.from_env()





def get_asns():
    asns = []
    with open("/home/ubuntu/bt/bwtester_stress_test/asns","r") as f:
        asns_str = f.read()

    asns = asns_str.split(",")

    return asns


def createContainerName(asn):
    return f"as{asn}h-bwtest-10.{asn}.0.30"

def runBWClient(src_asn, dst_asn, parameter_str = "3,?,?,500kbps"):
    bwClientCmd = """ bash -c "scion-bwtestclient -s {other_addr}:{other_port} -cs {cs_str} -sc {sc_str} > /var/log/{logfile}" """
    
    isd = int(str(dst_asn)[0])

    server_addr = f"{isd}-{dst_asn},10.{dst_asn}.0.30"
    server_port = "40002"

    client_cnt_name = createContainerName(src_asn)

    logfile_name = f"test_bwtestclient-{src_asn}-{dst_asn}.log"

    cmd = bwClientCmd.format(other_addr=server_addr, other_port=server_port, cs_str=parameter_str, sc_str=parameter_str, logfile=logfile_name)
    cnt = client.containers.get(client_cnt_name)
    cnt.exec_run(cmd, detach=True)
    

def allToAll(f):
    asns = get_asns()
    n = len(asns)
    with tqdm(total=n*n, desc=f"Running All To All Test on {str(f)}", unit="processes") as pbar:
        for client_asn in asns:
            for server_asn in asns:
                f(client_asn, server_asn)
                pbar.update(1)

def oneToAll(f, src_asn):
    asns = get_asns()
    n = len(asns)
    with tqdm(total=n, desc=f"Running One To All Test on {str(f)}", unit="processes") as pbar:
        for server_asn in asns:
            f(src_asn, server_asn)
            pbar.update(1)
        
def oneToOne(f, src_asn, dst_asn):
    print(f"Running One To One Test on {str(f)}")
    f(src_asn, dst_asn)

bwtest = TestFunction(runBWClient, "bwtester", parameter_str="3,?,?,1Gbps")

oneToOne(bwtest, 110, 120)

