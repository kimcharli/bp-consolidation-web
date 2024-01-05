import { GlobalEventEnum, globalData, CkIDB } from "./common.js";

const template = document.createElement("template");
template.innerHTML = `
    <style>
        table {
            width: 100%;
            border: 1px solid black;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            text-align: left;
        }
        th, .th {
            background-color: var(--global-th-color);
        }
    </style>

    <div id="gs-header" class="th">Links</div>
    <table id="main-table">
    <tr>
        <th id="num_links">#</th>
        <th>LABEL</th>
        <th>New LABEL</th>
        <th>speed</th>
        <th>AE</th>
        <th>CTs</th>
        <th>server-intf</th>
        <th>switch</th>
        <th>switch-intf</th>
    </tr>
    
    </table>
`

class GenericSystems extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        window.addEventListener(GlobalEventEnum.SYNC_STATE, this.handleSyncState.bind(this));

    }


    handleSyncState(event) {
        const table = this.shadowRoot.getElementById("main-table");

        const gs_count = Object.entries(globalData.servers).length;
        for (const server in globalData.servers) {
            const server_data = globalData.servers[server]
            let the_first = true;
            for (const link in server_data['links']) {
                const link_data = server_data['links'][link]
                const row = table.insertRow(-1);
                const link_count = Object.entries(server_data['links']).length;
                const line_counter = table.rows.length -1;

                row.insertCell(-1).innerHTML = line_counter;
                if (link_count > 1) {
                    if (the_first) {
                        const cell = row.insertCell(-1);
                        cell.innerHTML = server;
                        cell.setAttribute('rowspan', link_count);
                        // the_first = false;
                    }
                } else {
                    row.insertCell(-1).innerHTML = server;
                }
                if (link_count > 1) {
                    if (the_first) {
                        const cell = row.insertCell(-1);
                        cell.innerHTML = '';
                        cell.setAttribute('rowspan', link_count);
                        the_first = false;
                    }
                } else {
                    row.insertCell(-1).innerHTML = '';
                }
                row.insertCell(-1).innerHTML = link_data.speed;
                row.insertCell(-1).innerHTML = link_data.ae;
                const cts_cell = row.insertCell(-1);
                cts_cell.innerHTML = '';
                cts_cell.setAttribute('id', `cts-${line_counter}`)
                row.insertCell(-1).innerHTML = link_data.server_intf;
                row.insertCell(-1).innerHTML = link_data.switch;
                row.insertCell(-1).innerHTML = link_data.switch_intf;
            }
            
        };
        this.shadowRoot.getElementById("num_links").innerHTML = table.rows.length -1;
        this.shadowRoot.getElementById("gs-header").innerHTML = `${gs_count} Generic Systems, ${table.rows.length -1} Links`;
    }
}
customElements.define("generic-systems", GenericSystems);
