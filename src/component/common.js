

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
    static CONNECT_REQUEST = 'global-connect-request';
    static CONNECT_SUCCESS = 'global-connect-success';
    static CONNECT_LOGOUT = 'global-connect-logout';
    static SYNC_STATE_REQUEST = 'global-sync-state-request';
    static BP_CONNECT_REQUEST = 'blueprint-connect-request';
}