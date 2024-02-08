

const eventSource = new EventSource("/sse");
console.log('eventSource', eventSource);


eventSource.addEventListener('data-state', (event) => {
    const data = JSON.parse(event.data);
    const date = new Date();
    const timestamp = `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
    console.log(`sse data-state at ${timestamp} data=${data}`)
    const target = document.getElementById(data.id);
    // console.log('sse data-state', target)
    try {
        if (data.state !== null) target.dataset.state = data.state;
        // null check undefined too
        if (data.value !== null) target.innerHTML = data.value;
        if (data.visibility !== null) target.style.visibility = data.visibility;
        if (data.href !== null) target.href = data.href;
        if (data.target !== null) target.target = data.target;
        if (data.disabled != null) target.disabled = data.disabled;
    } catch (error) {
        console.log('sse data-state error', error, 'for data', data)
    }
});

eventSource.addEventListener('tbody-gs', (event) => {
    const data = JSON.parse(event.data);
    console.log('sse tbody-gs', data)
    const the_table = document.getElementById('generic-systems-table');
    let tbody = document.getElementById(data.id);
    if ( tbody == null ) {
        tbody = the_table.createTBody();
        tbody.setAttribute('id', data.id);
    }
    if (data.value !== null) tbody.innerHTML = data.value;
});


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
        vn_button.setAttribute('class', 'data-state');
        vns_div.append(vn_button);
    }
    if (data.state !== null) vn_button.dataset.state = data.state;

    vn_button.innerHTML = data.value;
    // window.scrollTo(0, document.body.scrollHeight);
});        



// window.addEventListener("load", (event) => {
//     console.log("page is fully loaded");


//     // const uploadFileButton = new UploadFileButton();
//     console.log('added syncStateButton')
//     const migrateAccessSwitchesButton = new MigrateAccessSwitchesButton();
//     const migrateGenericSystemsButton = new MigrateGenericSystemsButton();
//     // const migrateVirtualNetworksButtion = new MigrateVirtualNetworksButton();
//     // const migrateCTsButton = new MigrateCTsButton();
//     const compareConfigsButton = new CompareConfigsButton();
//     // CkIDB.openDB(connectButton);

// });

