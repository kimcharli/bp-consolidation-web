
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
            console.log(`openDB: data=`, data)
            if (typeof data !== 'undefined') {
                fetch('/update-env-ini', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                })
                .then(result => {
                    if(!result.ok) {
                        return result.text().then(text => { throw new Error(text) });
                    }
                    else { return result.json(); }
                })
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
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.FETCH_ENV_INI, { detail: data } )
        );
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.CONNECT_SERVER)
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


class GlobalData {
    // #switches = null;
    // #peer_link = null;
    // #servers = null;
    update(data) {
        this.peer_link = JSON.parse(JSON.stringify(data.peer_link));
        this.switches = JSON.parse(JSON.stringify(data.switches));
        this.servers = JSON.parse(JSON.stringify(data.servers));
        this.vnis = JSON.parse(JSON.stringify(data.vnis));
        console.log('GlobalData:update', this);
        window.dispatchEvent( new CustomEvent(GlobalEventEnum.SYNC_STATE) );
    }
    
}

export const globalData = new GlobalData();

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
    static SYNC_STATE = 'global-sync-state-request';
    static CONNECT_BLUEPRINT = 'blueprint-connect-request';
}