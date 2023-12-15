

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
}

export class GlobalEventEnum {
    static FETCH_ENV_INI = 'global-fetch-env-ini-request';  // 1. trigger by side-bar.js, action by apstra-server.js
    static FETCH_BP_REQUEST = 'global-fetch-bp-ini-request';  // 2. trigger by apstra-server.js, action by blueprint.js
    static CONNECT_REQUEST = 'global-connect-request';  // 3. trigger by side-bar.js, action by apstra-server.js
    static CONNECT_SUCCESS = 'global-connect-success';
    static CONNECT_LOGOUT = 'global-connect-logout';
    static SYNC_STATE_REQUEST = 'global-sync-state-request';
    static BP_CONNECT_REQUEST = 'blueprint-connect-request';
}