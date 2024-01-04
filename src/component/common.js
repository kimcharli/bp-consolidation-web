
// import Dexie from '../static/js/dexie.js';

// const LSPrefix = 'ckconweb:'

// // wildcard click event listener for debugging purpose
// document.addEventListener('click', function (e) {
//     console.log(`Global click event: ${this}, ${e}, id: ${e.currentTarget.id}`);
// });

// wildcard click event listener for debugging purpose
document.addEventListener('change', function (e) {
    console.log(`Global change event: ${this}, ${e}, id: ${e.currentTarget.id}`);
});


// IndexedDB
// https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB
export class CkIDB {
    static db = null;
    static serverStore = null;

    static openDB() {
        // console.log('openDB: Dexie', Dexie);
        this.db = new Dexie('ConsolidationDatabase');
        this.db.version(1).stores({
            apstra_server:
                `++id, 
                [host+port+username], 
                password`,
        });
        this.db.apstra_server.toCollection().first(data => {
            if (typeof data !== 'undefined') {
                this.TriggerFetchEnvIni(data);
            }
        })
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
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.FETCH_ENV_INI, { detail: data } )
        );
    }

    static trashEnv() {
        const transaction = this.db.transaction('rw', this.db.apstra_server, async () => {
            const servers = await this.db.apstra_server.clear();
        }).then(() => {
                console.log(`transaction completed`);
                window.dispatchEvent(
                    new CustomEvent(GlobalEventEnum.CLEAR_ENV_INI, { bubbles: true, composed: true } )
                );        
            }).catch(err => {
                console.log(`transaction failed -`, err);
        })
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.DISCONNECT_SERVER)
        );
    }
}


window.onload = function () {
    CkIDB.openDB();

}

export class GlobalEventEnum {
    // static LOADED_SERVER_DATA = 'global-loaded-server-data';  // 1. triggered by common.js, action by side-bar.js
    static FETCH_ENV_INI = 'global-fetch-env-ini-request';  // 1. trigger by side-bar.js, action by apstra-server.js
    static CLEAR_ENV_INI = 'global-clear-env-ini'
    // static FETCH_BP_REQUEST = 'global-fetch-bp-ini-request';  // 2. trigger by apstra-server.js, action by blueprint.js
    static CONNECT_SERVER = 'global-connect-request';  // 3. trigger by side-bar.js, action by apstra-server.js
    static DISCONNECT_SERVER = 'global-disconnect-request';  // 3. trigger by side-bar.js, action by apstra-server.js
    static CONNECT_SUCCESS = 'global-connect-success';
    static CONNECT_LOGOUT = 'global-connect-logout';
    static SYNC_STATE_REQUEST = 'global-sync-state-request';
    static CONNECT_BLUEPRINT = 'blueprint-connect-request';
}