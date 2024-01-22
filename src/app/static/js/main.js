


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
        // console.log('ConnectButton: constructor() this.button=', this.button);
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
                document.getElementById('sync-state').click();
            })
        )
    }
    
};

class SyncStateButton {
    constructor() {
        this.button = document.getElementById('sync-state');
        this.button.addEventListener('click', this.handleSyncState.bind(this));
    }

    handleSyncState(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/update-access-switches-table', {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            console.log('/update-access-switches-table', data)
            // globalData.update(data);
            data.values.forEach(element => {
                // console.log('element=', element)
                const the_element = document.getElementById(element.id);
                if (element.value) the_element.innerHTML = element.value;
                if (element.state) the_element.dataset.state = element.state;
                if (element.fill) the_element.style.fill = element.fill;
                if (element.visibility) the_element.style.visibility = element.visibility;
            })
            srcButton.dataset.state = 'done';
            document.getElementById("migrate-access-switches").dataset.state = data.button_state;
            // this.buttonMigrateAccessSwitches.dataset.state = data.button_state;
        })
        .catch(error => console.error('handleSyncStateClick - Error:', error, error.name, error.message));
        srcButton.dataset.state="loading";


        fetch('/update-generic-systems-table', {
            method: 'GET',
        })
        .then(result => {
            if(!result.ok) {
                return result.text().then(text => { throw new Error(text) });
            }
            else {
                return result.json();
            }
        })
        .then(data => {
            /*
                values: [
                    id: id to apply (tbody),
                    value: html-string
                ]
                caption: the caption of the table
            */
            console.log('handleSyncStateClick, /update-generic-systems-table, data=', data);
            const the_table = document.getElementById('generic-systems-table');
            data.values.forEach(element => {
                // console.log('tbody=', document.getElementById(element.id));
                let tbody = document.getElementById(element.id);
                if ( tbody == null ) {
                    tbody = the_table.createTBody();
                    tbody.setAttribute('id', element.id);
                }
                tbody.dataset.newId = element.newId;
                tbody.innerHTML = element.value;
            });
            the_table.caption.innerHTML = data.caption;
        })
        // .catch(error => console.error('handleSyncStateClick - Error:', error));

        fetch('/update-virtual-networks-data', {
            method: 'GET',
        })
        .then(result => {
            if(!result.ok) {
                return result.text().then(text => { throw new Error(text) });
            }
            else {
                return result.json();
            }
        })
        .then(data => {
            /*
                values: [
                    attrs: [ { name:, value } ]
                    value: button text
                ]
            */
            console.log('handleSyncStateClick, /update-virtual-networks-data, data=', data);
            const vns_div = document.getElementById('virtual-networks');
            data.values.forEach(element => {
                const vn_button = document.createElement("button");
                element.attrs.forEach(attr => {
                    vn_button.setAttribute(attr.attr, attr.value)
                })
                vn_button.appendChild(document.createTextNode(element.value));
                vns_div.append(vn_button);
                });
            const vn_caption = document.getElementById('virtual-networks-caption');
            vn_caption.innerHTML = data.caption;
        })
        // .catch(error => console.error('handleSyncStateClick - Error:', error));

    }

};


class MigrateAccessSwitchesButton {
    constructor() {
        this.button = document.getElementById('migrate-access-switches');
        this.button.addEventListener('click', this.handleMigrateAccessSwitches.bind(this));
        // console.log('MigrateAccessSwitches: constructor() this.button=', this.button);
    }

    handleMigrateAccessSwitches(event) {
        const srcButton = event.srcElement || event.target;
        fetch('/migrate-access-switches', {
            method: 'GET',
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
        // console.log('MigrateGenericSystemsButton: constructor() this.button=', this.button);
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
                tbody.innerHTML = data.value;
            })
            .catch(error => {
                console.log('handleMigrateAccessSwitchesClick - Error:', error);
                srcButton.dataset.state="error";  
            });
            tbody.getElementsByClassName('new_label')[0].dataset.state="loading";
        })
        // srcButton.dataset.state="loading";        
        
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

        // console.log('ConnectButton=', ConnectButton);
        this.connectButton.button.click();
        // ConnectButton.click();
        // document.getElementById('connect-server').click();
        // window.dispatchEvent(
        //     new CustomEvent(GlobalEventEnum.CONNECT_SERVER)
        // );
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



window.addEventListener("load", (event) => {
    console.log("page is fully loaded");
    const uploadFileButton = new UploadFileButton();
    const connectButton = new ConnectButton();
    const trashButton = new TrashButton();
    const syncStateButton = new SyncStateButton();
    const migrateAccessSwitchesButton = new MigrateAccessSwitchesButton();
    const migrateGenericSystemsButton = new MigrateGenericSystemsButton();
    CkIDB.openDB(connectButton);

});

