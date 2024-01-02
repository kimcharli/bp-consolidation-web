
// import Dexie from '../static/js/dexie.js';

// const LSPrefix = 'ckconweb:'

// wildcard click event listener for debugging purpose
document.addEventListener('click', function (e) {
    console.log(`Global click event: ${this}, ${e}, id: ${e.currentTarget.id}`);
});


// IndexedDB
// https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB
export class CkIDB {
    static db = null;
    static serverStore = null;

    static openDB() {
        console.log('openDB: Dexie', Dexie);
        this.db = new Dexie('ConsolidationDatabase');
        this.db.version(1).stores({
            apstra_server:
                `++id, 
                [host+port+username], 
                password`,
        });
        console.log('openDB: ', this.db);

    }

    static getServerStore() {
        return this.db.apstra_server.toCollection().first();
    }

    // triggered by side-bar
    static addServerStore(data) {
        this.db.apstra_server.put(data)
    }

}


// export const db = new Dexie('consolidation-db');


window.onload = function () {
    CkIDB.openDB();

}


export function queryFetch(query, variables){
    return fetch('/graphql', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/graphql-response+json',
         },
        body: JSON.stringify({
            query: query,
            variables: variables
        })
    })
    .then(res => res.json())
    .catch(err => console.error(`Error: queryFetch(${query}, ${variables}):`, err));
}

export class GlobalEventEnum {
    static LOADED_SERVER_DATA = 'global-loaded-server-data';  // 1. triggered by common.js, action by side-bar.js
    static FETCH_ENV_INI = 'global-fetch-env-ini-request';  // 1. trigger by side-bar.js, action by apstra-server.js
    // static FETCH_BP_REQUEST = 'global-fetch-bp-ini-request';  // 2. trigger by apstra-server.js, action by blueprint.js
    static CONNECT_REQUEST = 'global-connect-request';  // 3. trigger by side-bar.js, action by apstra-server.js
    static CONNECT_SUCCESS = 'global-connect-success';
    static CONNECT_LOGOUT = 'global-connect-logout';
    static SYNC_STATE_REQUEST = 'global-sync-state-request';
    static BP_CONNECT_REQUEST = 'blueprint-connect-request';
}