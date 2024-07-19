import express from 'express';
import { SocketHandler } from '../../utils/socket-handler';
import dockerode from 'dockerode';
import { SeedContainerInfo, Emulator, SeedNetInfo } from '../../utils/seedemu-meta';
import { Sniffer } from '../../utils/sniffer';
import WebSocket from 'ws';
import { Controller } from '../../utils/controller';

const router = express.Router();
const docker = new dockerode();
const socketHandler = new SocketHandler(docker);
const sniffer = new Sniffer(docker);
const controller = new Controller(docker);

const getContainers: () => Promise<SeedContainerInfo[]> = async function() {
    var containers: dockerode.ContainerInfo[] = await docker.listContainers();

    var _containers: SeedContainerInfo[] = containers.map(c => {
        var withMeta = c as SeedContainerInfo;

        withMeta.meta = {
            hasSession: socketHandler.getSessionManager().hasSession(c.Id),
            emulatorInfo: Emulator.ParseNodeMeta(c.Labels)
        };

        return withMeta;
    });

    // filter out undefine (not our nodes)
    return _containers.filter(c => c.meta.emulatorInfo.name);;
} 

socketHandler.getLoggers().forEach(logger => logger.setSettings({
    minLevel: 'warn'
}));

sniffer.getLoggers().forEach(logger => logger.setSettings({
    minLevel: 'warn'
}));

controller.getLoggers().forEach(logger => logger.setSettings({
    minLevel: 'warn'
}));

router.get('/network', async function(req, res, next) {
    var networks = await docker.listNetworks();

    var _networks: SeedNetInfo[] = networks.map(n => {
        var withMeta = n as SeedNetInfo;

        withMeta.meta = {
            emulatorInfo: Emulator.ParseNetMeta(n.Labels)
        };

        return withMeta;
    });
    
    _networks = _networks.filter(n => n.meta.emulatorInfo.name);

    res.json({
        ok: true,
        result: _networks
    });

    next();
});

router.get('/container', async function(req, res, next) {
    try {
        let containers = await getContainers();

        res.json({
            ok: true,
            result: containers
        });
    } catch (e) {
        res.json({
            ok: false,
            result: e.toString()
        });
    }

    next();
});

router.get('/container/:id', async function(req, res, next) {
    var id = req.params.id;

    var candidates = (await docker.listContainers())
        .filter(c => c.Id.startsWith(id));

    if (candidates.length != 1) {
        res.json({
            ok: false,
            result: `no match or multiple match for container ID ${id}.`
        });
    } else {
        var result: any = candidates[0];
        result.meta = {
            hasSession: socketHandler.getSessionManager().hasSession(result.Id),
            emulatorInfo: Emulator.ParseNodeMeta(result.Labels)
        };
        res.json({
            ok: true, result
        });
    }

    next();
});

router.get('/container/:id/net', async function(req, res, next) {
    let id = req.params.id;

    var candidates = (await docker.listContainers())
        .filter(c => c.Id.startsWith(id));

    if (candidates.length != 1) {
        res.json({
            ok: false,
            result: `no match or multiple match for container ID ${id}.`
        });
        next();
        return;
    }

    let node = candidates[0];

    res.json({
        ok: true,
        result: await controller.isNetworkConnected(node.Id)
    });

    next();
});

router.post('/container/:id/net', express.json(), async function(req, res, next) {
    let id = req.params.id;

    var candidates = (await docker.listContainers())
        .filter(c => c.Id.startsWith(id));

    if (candidates.length != 1) {
        res.json({
            ok: false,
            result: `no match or multiple match for container ID ${id}.`
        });
        next();
        return;
    }
    
    let node = candidates[0];

    controller.setNetworkConnected(node.Id, req.body.status);
    
    res.json({
        ok: true
    });

    next();
});

router.ws('/console/:id', async function(ws, req, next) {
    try {
        await socketHandler.handleSession(ws, req.params.id);
    } catch (e) {
        if (ws.readyState == 1) {
            ws.send(`error creating session: ${e}\r\n`);
            ws.close();
        }
    }
    
    next();
});

var snifferSubscribers: WebSocket[] = [];
var currentSnifferFilter: string = '';

router.post('/sniff', express.json(), async function(req, res, next) {
    sniffer.setListener((nodeId, data) => {
        var deadSockets: WebSocket[] = [];

        snifferSubscribers.forEach(socket => {
            if (socket.readyState == 1) {
                socket.send(JSON.stringify({
                    source: nodeId, data: data.toString('utf8')
                }));
            }

            if (socket.readyState > 1) {
                deadSockets.push(socket);
            }
        });

        deadSockets.forEach(socket => snifferSubscribers.splice(snifferSubscribers.indexOf(socket), 1));
    });

    currentSnifferFilter = req.body.filter ?? '';

    await sniffer.sniff((await getContainers()).map(c => c.Id), currentSnifferFilter);

    res.json({
        ok: true,
        result: {
            currentFilter: currentSnifferFilter
        }
    });

    next();
});

router.get('/sniff', function(req, res, next) {
    res.json({
        ok: true,
        result: {
            currentFilter: currentSnifferFilter
        }
    });

    next();
});

router.ws('/sniff', async function(ws, req, next) {
    snifferSubscribers.push(ws);
    next();
});

router.get('/container/:id/bgp', async function (req, res, next) {
    let id = req.params.id;

    var candidates = (await docker.listContainers())
        .filter(c => c.Id.startsWith(id));

    if (candidates.length != 1) {
        res.json({
            ok: false,
            result: `no match or multiple match for container ID ${id}.`
        });
        next();
        return;
    }

    let node = candidates[0];

    res.json({
        ok: true,
        result: await controller.listBgpPeers(node.Id)
    });

    next();
});

router.post('/container/:id/bgp/:peer', express.json(), async function (req, res, next) {
    let id = req.params.id;
    let peer = req.params.peer;

    var candidates = (await docker.listContainers())
        .filter(c => c.Id.startsWith(id));

    if (candidates.length != 1) {
        res.json({
            ok: false,
            result: `no match or multiple match for container ID ${id}.`
        });
        next();
        return;
    }

    let node = candidates[0];

    await controller.setBgpPeerState(node.Id, peer, req.body.status);

    res.json({
        ok: true
    });

    next();
});


function parseRate(rate: string, metric: string): string {
    let result = rate;

    if (metric == 'Kbit') {
        result = (parseInt(rate) * 1000).toString();
    }
    else if (metric == 'Mbit') {
        result = (parseInt(rate) * 1000000).toString();
    }  
    else if (metric == 'Gbit') {
        result = (parseInt(rate) * 1000000000).toString();
    }
    else if (metric == 'Tbit') {
        result = (parseInt(rate) * 1000000000000).toString();
    }
    return result;
}

router.get('/network/:id/tc',  async function(req, res, next) {
    // get container attached to network
    var containers = await docker.listContainers();
    var container = containers.find(c => {
        const nets = c.NetworkSettings.Networks;
        return Object.keys(nets).some(n => nets[n].NetworkID.startsWith(req.params.id));
    });


    var net = (await docker.listNetworks()).filter(n => n.Id.startsWith(req.params.id))[0];
    var ifname = net.Labels['org.seedsecuritylabs.seedemu.meta.name'];
    
    // exectue tc qdisc show dev $id
    const exec = await docker.getContainer(container.Id).exec({
        Cmd: ['tc', 'qdisc', 'show', 'dev', ifname],
        AttachStdout: true,
        AttachStderr: true
    });

    const stream = await exec.start({ hijack: true, stdin: true });

    let result = '';
    stream.on('data', (data) => {
        result += data.toString();
    });

    await new Promise((resolve, reject) => {
        stream.on('end', resolve);
        stream.on('error', reject);
    });

    // parse the result
    // Format: qdisc netem 803a: dev $ifname root refcnt 5 limit 100 delay 100.0ms loss 5% rate 1Tbit

    // use regex to extract the limit
    const limit = result.match(/limit (\d+) /)?.[1];

    const latencyMatch = result.match(/delay (\d+)(?:\.(\d+))?(ms|us|ns|s)/);
    let latency;
    if (latencyMatch) {
        let value = parseFloat(`${latencyMatch[1]}${latencyMatch[2] ? '.' + latencyMatch[2] : ''}`);
        let unit = latencyMatch[3];
        switch (unit) {
            case 'us':
                value /= 1000;
                break;
            case 'ns':
                value /= 1000000;
                break;
            case 's':
                value *= 1000;
                break;
        }
        latency = value;
    }

    
    
    const loss = result.match(/loss (\d+)%/)?.[1];    

    // rate is in bit/s
    let rate = result.match(/rate (\d+)(bit|Mbit|Kbit|Gbit|Tbit)/)?.[1];
    // convert rate to bit/s
    const metric = result.match(/rate (\d+)(bit|Mbit|Kbit|Gbit|Tbit)/)?.[2];

    rate = parseRate(rate, metric);



    const parsed_result = {
        queue: limit,
        latency,
        loss,
        bw: rate
    }

    // return the result
    res.json({
        ok: true,
        result: parsed_result
    });
    next();
});

router.post('/network/:id/tc', express.json(), async function(req, res, next) {
    const { bw, latency, loss, queue } = req.body;

    // get network by id
    var net = (await docker.listNetworks()).filter(n => n.Id.startsWith(req.params.id))[0];
    var ifname = net.Labels['org.seedsecuritylabs.seedemu.meta.name'];
    
    // get containers attached to the network
    var containers = (await docker.listContainers()).filter(c => {
        const nets = c.NetworkSettings.Networks;
        return Object.keys(nets).some(n => nets[n].NetworkID.startsWith(req.params.id));
    });

    // execute tc command on each container
    
    const cmd = ['tc', 'qdisc', 'replace', 'dev', ifname, 'root', 'netem'];
    
    // if value is -, dont put it in the command
    if (bw === '-1' && latency === '-1' && loss === '-1' && queue === '-1') {
        res.json({
            ok: true,
            result: 'no change'
        });
        next();
        return;
    }

    if (bw != '-1') {
        cmd.push('rate', `${bw}bit`);
    }
    if (latency != '-1') {
        cmd.push('latency', `${latency}ms`);
    }
    if (loss != '-1') {
        cmd.push('loss', `${loss}%`);
    }
    if (queue != '-1') {
        cmd.push('limit', `${queue}`);
    }


    let results = [];

    for (let container of containers) {
        const exec = await docker.getContainer(container.Id).exec({
            Cmd: cmd,
            AttachStdout: true,
            AttachStderr: true
        });

        const stream = await exec.start({ hijack: true, stdin: true });

        let result = '';
        stream.on('data', (data) => {
            result += data.toString();
        });

        await new Promise((resolve, reject) => {
            stream.on('end', resolve);
            stream.on('error', reject);
        });

        results.push(result);
    }

    res.json({
        ok: true,
        result: results
    });
    next();
});

export = router;