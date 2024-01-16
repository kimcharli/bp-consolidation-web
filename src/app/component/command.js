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

        this.shadowRoot.getElementById('connect-button').addEventListener('click', () => {
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
        window.addEventListener(GlobalEventEnum.FETCH_ENV_INI, () => {
            this.shadowRoot.getElementById('load-env-div').dataset.loaded = 'loaded';
        });
        window.addEventListener(GlobalEventEnum.CLEAR_ENV_INI, () => {
            this.shadowRoot.getElementById('load-env-div').dataset.loaded = '';
        });
        window.addEventListener(GlobalEventEnum.CONNECT_SUCCESS, this.handleConnectSuccess.bind(this));
        window.addEventListener(GlobalEventEnum.CONNECT_SERVER, () => {
            this.shadowRoot.getElementById('connect-button').dataset.state = 'loading';
        });
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


    handleConnectSuccess(event) {
        // console.log('handleConnectSuccess' + event.detail + ' ' + this.connect_items)
        this.connect_items = this.connect_items.filter((item) => item !== event.detail.name)
        if (this.connect_items.length === 0) {
            this.shadowRoot.getElementById('connect-button').dataset.state = 'done';
        }
    }

    handleServerLogout(event) {
        this.shadowRoot.getElementById('connect-button').dataset.state = 'init';
    }

    handleSyncStateClick(event) {
        fetch('/pull-data', {
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
            globalData.update(data);
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
            this.buttonMigrateGenericSystems.dataset.state="done";  
        })
        .catch(error => {
            console.log('handleMigrateAccessSwitchesClick - Error:', error);
            this.buttonMigrateGenericSystems.dataset.state="error";  
        });
        this.buttonMigrateGenericSystems.dataset.state="loading";
    }
}   
customElements.define('side-bar', SideBar);