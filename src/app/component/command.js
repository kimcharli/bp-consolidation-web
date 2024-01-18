import { GlobalEventEnum, globalData, CkIDB } from "./common.js";

// TODO: use variable in template
const MIGRATE_GENERIC_SYSTEMS = 'migrate-generic-systems';

const template = document.createElement("template");
template.innerHTML = `
    <style>
        div {
            background: green;
            width: 180px;
            hight: max-content;
        }
        button {
            background-color: var(--global-warning-color);
            text-align: left;
            // border: none;
            // color: white;
            // padding: 15px 32px;
            // text-align: left;
            // text-decoration: none;
            // display: block;
            // font-size: 16px;
            width: 100%;
        }
        img {
            width: 20px;
            height: 20px;
            background-color: white;
        }
        #load-env-div {
            font-family: Arial, Helvetica, sans-serif;
        }
        #load-env-div[data-loaded=""] {
            background-color: var(--global-warning-color);
        }
        #load-env-div[data-loaded="loaded"] {
            background-color: var(--global-ok-color);
        }

        @keyframes pulse {
            0%, 49% {
            color: white;
            }
            50%, 100% {
            color: transparent;
            }
        }

        .data-state[data-state="init"] {
            background-color: var(--global-warning-color);
        }
        .data-state[data-state="loading"] {
            animation: pulse 1s infinite
        }
        .data-state[data-state="done"] {
            background-color: var(--global-ok-color);
        }
        .data-state[data-state="error"] {
            background-color: var(--global-error-color);
        }
    
    </style>
    <h3>Commands</h3>
    <div>
        <div id="load-env-div" style="padding-left: 6px;padding-right: 6px;font-family: Arial;font-size: 14px;" data-loaded>
            Load
            <img id="trash-env" src="/images/trash.svg" alt="trash env" align="right" />
            <a href="/static/env-example.ini" download="env-example.ini"><img src="/images/download.svg" align="right" /></a>
            <img id="upload-env-ini-img" src="/images/upload.svg" alt="Upload ini" align="right" /><input type="file" id="upload-env-ini-input" style="display: none;">
        </div>
        <div>
            <button id="connect-button" type="button" data-state="init" class="data-state">Connect</button>
        </div>
        <div>
            <button id="sync-state" type="button" data-state="init" class="data-state">Sync States</button>
        </div>
        <div>
            <button id="migrate-access-switches" type="button" data-state="init" class="data-state">Migrate Access Switches</button>
        </div>
        <div>
            <button id="migrate-generic-systems" type="button" data-state="init" class="data-state">Migrate Generic Systems</button>
        </div>
        <div>
            <button type="button" data-state="init" class="data-state">Migrate Virtual Networks</button>
        </div>
        <div>
            <button type="button" data-state="init" class="data-state">Migrate CTs</button>
        </div>
        <div>
            <button type="button" data-state="init" class="data-state">Pull Configurations</button>
        </div>
        <div>
            <button type="button" data-state="init" class="data-state">Move Devices</button>
        </div>
    </div>
`

class SideBar extends HTMLElement {    
    constructor() {
        super();        
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        this.connect_items = ['server', 'main_bp', 'tor_bp'];  // to check all the connect_success
        // load env initiated
        this.shadowRoot.getElementById('upload-env-ini-img').addEventListener('click', this.handleUploadIniImageClick.bind(this));
        // upload submitted
        this.shadowRoot.getElementById('upload-env-ini-input').addEventListener('change', this.handleUploadIniInputChange.bind(this), false);
        this.shadowRoot.getElementById('trash-env').addEventListener('click', this.handleTrashEnv.bind(this));

        this.buttonConnectServer = this.shadowRoot.getElementById('connect-button');
        this.buttonConnectServer.addEventListener('click', () => {
            window.dispatchEvent(
                new CustomEvent(GlobalEventEnum.CONNECT_SERVER)
            );   
        });

        this.buttonSyncState = this.shadowRoot.getElementById('sync-state');
        this.buttonSyncState.addEventListener('click', this.handleSyncStateClick.bind(this));

        this.shadowRoot.getElementById('migrate-access-switches').addEventListener('click', this.handleMigrateAccessSwitchesClick.bind(this));

        this.buttonMigrateGenericSystems = this.shadowRoot.getElementById('migrate-generic-systems');
        this.buttonMigrateGenericSystems.addEventListener('click', this.handleMigrateGenericSystemsClick.bind(this));


        // window.addEventListener(GlobalEventEnum.LOAD_LOCAL_DATA, this.fetch_blueprint.bind(this));
        window.addEventListener(GlobalEventEnum.FETCH_ENV_INI, (event) => {
            const data = event.detail
            document.getElementById('apstra-host').value = data.host;
            document.getElementById('apstra-port').value = data.port;
            document.getElementById('apstra-username').value = data.username;
            document.getElementById('apstra-password').value = data.password;    
            document.getElementById('apstra-host').dataset.id = data.id;

            document.getElementById("main_bp").innerHTML = data.main_bp_label;
            document.getElementById("tor_bp").innerHTML = data.tor_bp_label;
    
            this.shadowRoot.getElementById('load-env-div').dataset.loaded = 'loaded';
        });
        window.addEventListener(GlobalEventEnum.CLEAR_ENV_INI, () => {
            this.shadowRoot.getElementById('load-env-div').dataset.loaded = '';
        });
        window.addEventListener(GlobalEventEnum.CONNECT_SUCCESS, this.handleConnectSuccess.bind(this));
        window.addEventListener(GlobalEventEnum.CONNECT_SERVER, this.handleConnectServer.bind(this));
        window.addEventListener(GlobalEventEnum.CONNECT_LOGOUT, this.handleServerLogout.bind(this));
    }

    // load env clicked
    handleUploadIniImageClick(event) {
        console.log('handleUploadIniImageClick() id =', event.currentTarget.id );
        this.shadowRoot.getElementById('upload-env-ini-input').click();
    }        

    handleTrashEnv(event) {
        CkIDB.trashEnv()
        this.handleServerLogout(event)
    }

    // upload submitted
    handleUploadIniInputChange(event) {
        console.log('handleUploadIniInputChange() id =', event.currentTarget.id );
        const input_element = this.shadowRoot.getElementById('upload-env-ini-input');
        const formData = new FormData();
        formData.append('file', input_element.files[0]);
        fetch('/upload-env-ini', {
            method: 'POST',
            body: formData
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
            console.log('handleUploadIniInputChange - fetched', data);
            CkIDB.addServerStore(data);
        })
        .catch(error => console.error('handleUploadIniInputChange - fetch Error:', error));
    }


    handleConnectServer(event) {
        console.log('handleConnectServer() begin')
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
        .then(result => {
            if(!result.ok) {
                return result.text().then(text => { throw new Error(text) });
            }
            else {
                return result.json();
            }
        })
        .then(data => {
            console.log('/login-server: Apstra version: ', data.version);
            this.connect_blueprint();
            this.buttonConnectServer.dataset.state = 'done';
        })
        .catch(error => {
            console.log(error);
        })
        this.buttonConnectServer.dataset.state = 'loading';

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
            .then(result => {
                if(!result.ok) {
                    return result.text().then(text => { throw new Error(text) });
                }
                else {
                    return result.json();
                }
            })
            .then(data => {
                console.log(`connect_blueprint then`, data)
                document.getElementById(element).dataset.id = data.id;
                document.getElementById(element).innerHTML = `<a href="${data.url}" target="_blank">${data.label}</a>`;
                document.getElementById(element).dataset.state = 'done';

                // auto continue to sync
                this.buttonSyncState.click();
            })
        )
    }


    handleConnectSuccess(event) {
        // console.log('handleConnectSuccess' + event.detail + ' ' + this.connect_items)
        this.connect_items = this.connect_items.filter((item) => item !== event.detail.name)
        if (this.connect_items.length === 0) {
            this.buttonConnectServer.dataset.state = 'done';
            // auto continue to sync
            console.log('auto-continue');
            this.buttonSyncState.click();
        }
    }

    handleServerLogout(event) {
        this.buttonConnectServer.dataset.state = 'init';
    }

    handleSyncStateClick(event) {
        // fetch('/pull-data', {
        //     method: 'GET',
        // })
        // .then(result => {
        //     if(!result.ok) {
        //         return result.text().then(text => { throw new Error(text) });
        //     }
        //     else {
        //         return result.json();
        //     }
        // })
        // .then(data => {
        //     globalData.update(data);
        //     this.buttonSyncState.dataset.state = 'done';
        // })
        // .catch(error => console.error('handleSyncStateClick - Error:', error));
        // this.buttonSyncState.dataset.state="loading";

        fetch('/update-access-switches-table', {
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
            // globalData.update(data);
            data.values.forEach(element => {
                console.log('element=', element)
                const the_element = document.getElementById(element.id);
                if (element.value) the_element.innerHTML = element.value;
                if (element.state) the_element.dataset.state = element.state;
                if (element.fill) the_element.style.fill = element.fill;
                if (element.visibility) the_element.style.visibility = element.visibility;
            })
            this.buttonSyncState.dataset.state = 'done';
        })
        .catch(error => console.error('handleSyncStateClick - Error:', error));
        this.buttonSyncState.dataset.state="loading";


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
                const tbody = the_table.createTBody();
                tbody.setAttribute('id', element.id);
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

    handleMigrateAccessSwitchesClick(event) {
        fetch('/migrate-access-switches', {
            method: 'POST',
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
            this.shadowRoot.getElementById('migrate-access-switches').dataset.state="done";  
        })
        .catch(error => console.error('handleMigrateAccessSwitchesClick - Error:', error));
        this.shadowRoot.getElementById('migrate-access-switches').dataset.state="loading";
    }

    handleMigrateGenericSystemsClick(event) {
        console.log(event)
        let done = false;
        while (done === false) {
            fetch('/migrate-generic-systems', {
                method: 'POST',
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
                    done: true/false
                    values: [
                        id: id of tbody,
                        value: html-string
                    ]
                    caption: the caption of the table
                */
                data.values.forEach(element => {
                    const tbody = document.getElementById(element.id);
                    tbody.innerHTML = element.value;
                });
                the_table.caption.innerHTML = data.caption;
                if (data.done) {
                    done = true;
                    this.buttonMigrateGenericSystems.dataset.state="done";  
                }
            })
            .catch(error => {
                console.log('handleMigrateAccessSwitchesClick - Error:', error);
                this.buttonMigrateGenericSystems.dataset.state="error";  
            });    
        }
        this.buttonMigrateGenericSystems.dataset.state="loading";
    }
}   
customElements.define('side-bar', SideBar);