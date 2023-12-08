

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

