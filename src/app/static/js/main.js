


class UploadFileButton {
    constructor() {
        document.getElementById('upload-env-ini-img')
            .addEventListener('click', () => document.getElementById('upload-env-ini-input').click());
        this.input = document.getElementById('upload-env-ini-input');
        this.input.addEventListener('change', this.handleUploadIniInputChange.bind(this), false);
    }

    handleUploadIniInputChange(event) {
        console.log('handleUploadIniInputChange() id =', event.currentTarget.id );
        const formData = new FormData();
        formData.append('file', this.input.files[0]);
        fetch('/upload-env-ini', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('handleUploadIniInputChange - fetched', data);
            CkIDB.addServerStore(data);
        })
        .catch(error => console.error('handleUploadIniInputChange - fetch Error:', error));
    }
};


class TrashButton {
    constructor(connectButton) {
        this.connectButton = connectButton;
        this.button = document.getElementById('trash-env');
        this.button.addEventListener('click', this.handleTrashEnv.bind(this));
    }

    handleTrashEnv(event) {
        CkIDB.trashEnv()
        document.getElementById('connect-button').dataset.state = 'init';
        // TODO: logout
        // TODO: cascade clear
    }

}

class ConnectButton {
    constructor() {
        this.button = document.getElementById('connect-button');
        this.button.addEventListener('click', this.handleConnectServer.bind(this));
    }

    handleConnectServer(event) {
        const srcButton = event.srcElement || event.target;
        // console.log('handleConnectServer() begin.. event=', event);
        const apstra_host = document.getElementById('apstra-host').value;
        const apstra_port = document.getElementById('apstra-port').value;
        const apstra_username = document.getElementById('apstra-username').value;
        const apstra_password = document.getElementById('apstra-password').value;
        fetch('/login-server', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                host: apstra_host,
                port: apstra_port,
                username: apstra_username,
                password: apstra_password                
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('/login-server: Apstra version: ', data.version);
            this.connect_blueprint();
            srcButton.dataset.state = 'done';
        })
        .catch(error => {
            console.log(error);
        })
        srcButton.dataset.state = 'loading';    
    }

    connect_blueprint() {
        ['main_bp', 'tor_bp'].forEach(element => 
            fetch('/login-blueprint', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label: document.getElementById(element).innerHTML,
                    role: element,
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log(`connect_blueprint then`, data)
                document.getElementById(element).dataset.id = data.id;
                document.getElementById(element).innerHTML = `<a href="${data.url}" target="_blank">${data.label}</a>`;
                document.getElementById(element).dataset.state = 'done';
    
                // auto continue to sync
            })
        );
        document.getElementById('sync-state').click();
    }
    
};

class SyncStateButton {
    constructor() {
        this.button = document.getElementById('sync-state');
        this.button.addEventListener('click', this.handleSyncState.bind(this));
    }

    handleSyncState(event) {
        const srcButton = event.srcElement || event.target;

        fetch('/sync', {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            console.log('/sync', data)
        })
        .catch(error => console.error('handleSyncState - Error:', error, error.name, error.message));
        this.button.dataset.state = 'loading';
    }

}


class MigrateAccessSwitchesButton {
    constructor() {
        this.button = document.getElementById('migrate-access-switches');
        this.button.addEventListener('click', this.handleMigrateAccessSwitches.bind(this));
    }

    handleMigrateAccessSwitches(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/migrate-access-switches', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            console.log('/migrate-access-switches', data)
            srcButton.dataset.state = 'done';
            document.getElementById("migrate-access-switches").dataset.state = data.button_state;
        })
        .catch(error => console.error('handleMigrateAccessSwitches - Error:', error, error.name, error.message));
        srcButton.dataset.state="loading";
    }
}


class MigrateGenericSystemsButton {
    constructor() {
        this.button = document.getElementById('migrate-generic-systems');
        this.button.addEventListener('click', this.handleMigrateGenericSystems.bind(this));
    }

    handleMigrateGenericSystems(event) {
        const srcButton = event.srcElement || event.target;
        Array.from(document.getElementById('generic-systems-table').getElementsByTagName('tbody'))
        .forEach(tbody => {
            const tbody_id = tbody.getAttribute('id');
            console.log('migrate generic system begin - tbody_id', tbody_id)
            fetch('/migrate-generic-system', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tbody_id: tbody_id,
                })
            })
            .then(response => response.json())
            .then(data => {
                /*
                    done: true/false
                    values: [
                        id: id of tbody,
                        value: html-string
                    ]
                    caption: the caption of the table
                */
                console.log('migrate generic system data for', tbody_id, '=', data)
                // tbody.innerHTML = data.value;
                // if (data.done) document.getElementById('migrate-generic-systems').dataset.state = 'done';
            })
            .catch(error => {
                console.log('handleMigrateAccessSwitchesClick - Error:', error);
                srcButton.dataset.state="error";  
            });
            const new_label_element = tbody.getElementsByClassName('new_label')[0];
            // console.log(new_label_element)
            new_label_element.dataset.state="loading";
        })
        // TODO: 
        // this.button.dataset.state = 'done';
        //     if (data.done) document.getElementById('migrate-generic-systems').dataset.state = 'done';
        
    }
}


class MigrateVirtualNetworksButton {
    constructor() {
        this.button = document.getElementById('migrate-virtual-networks');
        this.button.addEventListener('click', this.handleMigrateVirtualNetworks.bind(this));
   }

    handleMigrateVirtualNetworks(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/migrate-virtual-networks', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('migrate-virtual-networks data=', data)
        })
        .catch(error => {
            console.log('handleMigrateAccessSwitchesClick - Error:', error);
            srcButton.dataset.state="error";
        });    
        this.button.dataset.state = 'loading';
    }
}


class MigrateCTsButton {
    constructor() {
        this.button = document.getElementById('migrate-cts');
        this.button.addEventListener('click', this.handleMigrateCTs.bind(this));
   }

    handleMigrateCTs(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/migrate-cts', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('/migrate-cts data=', data)
            // this.button.dataset.state = 'done';
        })
        .catch(error => {
            console.log('handleMigrateCTs - Error:', error);
            srcButton.dataset.state="error";
        });    
        this.button.dataset.state = 'loading';
    }
}

class CompareConfigsButton {
    constructor() {
        this.button = document.getElementById('compare-config');
        this.button.addEventListener('click', this.handleCompareConfig.bind(this));
   }

    handleCompareConfig(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/compare-config', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('/compare-config data=', data)
            this.button.dataset.state = 'done';
        })
        .catch(error => {
            console.log('/compare-config - Error:', error);
            srcButton.dataset.state="error";
        });    
        this.button.dataset.state = 'loading';
    }
}


class CkIDB {
    static db = null;
    static serverStore = null;

    static openDB(connectButton) {
        this.connectButton = connectButton;
        // console.log('openDB: Dexie', Dexie);
        this.db = new Dexie('ConsolidationDatabase');
        this.db.version(1).stores({
            apstra_server:
                `++id, 
                [host+port+username], 
                password`,
        });
        this.db.apstra_server.toCollection().first(data => {
            console.log(`openDB: data=`, data)
            if (typeof data !== 'undefined') {
                fetch('/update-env-ini', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .catch(error => {
                    console.log(`error`, error)
                })
                console.log('openDB: invoke TriggerFetchEnvIni()')
                this.TriggerFetchEnvIni(data);
            }
        })
        .then(data => {
            console.log('ok');
         })
        .catch(err => console.log('err', err))
    }


    static isServerValid(data) {
        console.log('isServerValid() data.host =', data.host)
        return data.host && data.port && data.username && data.password
    }

    // triggered by side-bar
    static addServerStore(data) {
        console.log('addServerStore() data', data)
        if (this.isServerValid(data)) {
            console.log('addServerStore() - isServerValid')
            this.db.apstra_server.put(data)
            console.log('addServerStore() - invoke TriggerFetchEnvIni')
            this.TriggerFetchEnvIni(data);    
        } else {
            console.log('addServerStore() - invalid input')
        }
    }

    static TriggerFetchEnvIni(data) {
        // window.dispatchEvent(
        //     new CustomEvent(GlobalEventEnum.FETCH_ENV_INI, { detail: data } )
        // );

        document.getElementById('apstra-host').value = data.host;
        document.getElementById('apstra-port').value = data.port;
        document.getElementById('apstra-username').value = data.username;
        document.getElementById('apstra-password').value = data.password;    
        document.getElementById('apstra-host').dataset.id = data.id;

        document.getElementById("main_bp").innerHTML = data.main_bp_label;
        document.getElementById("tor_bp").innerHTML = data.tor_bp_label;

        document.getElementById('load-env-div').dataset.state = 'done';

        console.log('TriggerFetchEnvIni() - invoke connectButton.click()')
        this.connectButton.button.click();
    }

    static trashEnv() {
        const transaction = this.db.transaction('rw', this.db.apstra_server, async () => {
            const servers = await this.db.apstra_server.clear();
        }).then(() => {
                console.log(`transaction completed`);
                // window.dispatchEvent(
                //     new CustomEvent(GlobalEventEnum.CLEAR_ENV_INI, { bubbles: true, composed: true } )
                // );        
            }).catch(err => {
                console.log(`transaction failed -`, err);
        })
        // window.dispatchEvent(
        //     new CustomEvent(GlobalEventEnum.DISCONNECT_SERVER)
        // );
    }
}


const eventSource = new EventSource("/sse");
console.log('eventSource', eventSource);

eventSource.addEventListener('sse', (event) => {
    console.log('sse EventListener', event)
    console.log('sse EventListener', event.data);        // document.getElementById("server-time").innerHTML = event.data;
});

eventSource.addEventListener('data-state', (event) => {
    const data = JSON.parse(event.data);
    // console.log('sse data-state', data)
    const target = document.getElementById(data.id);
    // console.log('sse data-state', target)
    try {
        if (data.state !== undefined && data.state != null) target.dataset.state = data.state;
        // null check undefined too
        if (data.value !== null) target.innerHTML = data.value;
        if (data.visibility) target.style.visibility = data.visibility;
    } catch (error) {
        console.log('sse data-state error', error, 'for data', data)
    }
});

eventSource.addEventListener('tbody-gs', (event) => {
    const data = JSON.parse(event.data);
    const the_table = document.getElementById('generic-systems-table');
    let tbody = document.getElementById(data.id);
    if ( tbody == null ) {
        tbody = the_table.createTBody();
        tbody.setAttribute('id', data.id);
    }
    if (data.value !== null) tbody.innerHTML = data.value;
});


eventSource.addEventListener('disable-button', (event) => {
    const data = JSON.parse(event.data);
    // console.log('sse data-state', data)
    const target = document.getElementById(data.id);
    target.disabled = data.disabled;
});

eventSource.onmessage = (event) => {
    console.log('eventSource', event)
    console.log('eventSource.onmessage', event.data);        // document.getElementById("server-time").innerHTML = event.data;
};  

eventSource.addEventListener('update-vn', (event) => {
    const data = JSON.parse(event.data);
    // id: id of the button
    // attrs: [ { attr: , value: } ]
    // value: button text
    const vns_div = document.getElementById('virtual-networks');
    let vn_button = document.getElementById(data.id);
    if ( vn_button == null ) {
        vn_button = document.createElement("button");
        vn_button.setAttribute('id', data.id);
        vn_button.appendChild(document.createTextNode(data.value));
        vns_div.append(vn_button);
    }
    data.attrs.forEach(attr => {
        vn_button.setAttribute(attr.attr, attr.value)
    })
    vn_button.innerHTML = data.value;
    window.scrollTo(0, document.body.scrollHeight);
});        

eventSource.addEventListener('update-caption', (event) => {
    const data = JSON.parse(event.data);
    // id: id of the caption
    // value: caption text
    const the_caption = document.getElementById(data.id);
    the_caption.innerHTML = data.value;
});        

eventSource.addEventListener('ct-update', (event) => {
    const data = JSON.parse(event.data);
    // id: id of the button
    // attrs: [ { attr: , value: } ]
    // value: button text
    console.log('sse ct-update', data)
    const tbody = document.getElementById(data.id);  // tbody_id
    const target = tbody.getElementsByClassName('cts')[0];
    // console.log('sse update-vn', target)
    target.setAttribute('rowspan', data.rowspan)
    data.attrs.forEach(attr => {
        target.setAttribute(attr.attr, attr.value)
    })
    target.innerHTML = data.value;
});


window.addEventListener("load", (event) => {
    console.log("page is fully loaded");


    const uploadFileButton = new UploadFileButton();
    const connectButton = new ConnectButton();
    const trashButton = new TrashButton();
    console.log('added trashButton')
    const syncStateButton = new SyncStateButton();
    console.log('added syncStateButton')
    const migrateAccessSwitchesButton = new MigrateAccessSwitchesButton();
    const migrateGenericSystemsButton = new MigrateGenericSystemsButton();
    const migrateVirtualNetworksButtion = new MigrateVirtualNetworksButton();
    const migrateCTsButton = new MigrateCTsButton();
    const compareConfigsButton = new CompareConfigsButton();
    CkIDB.openDB(connectButton);

});

