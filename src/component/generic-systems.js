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
        <th>AE</th>
        <th>CTs</th>
        <th>speed</th>
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
            const server_data = globalData.servers[server];
            // console.log(`handleSyncState: server=${server}, server_data`, server_data);
            let first_in_server = true;
            let server_rowspan = 0;
            for (const ae in server_data) {
                // console.log(`handleSyncState: ae=${ae}`, server_data[ae]['links']);
                server_rowspan += server_data[ae]['links'].length;
            }
            // console.log(`server: ${server} server_rowspan: ${server_rowspan}`);
            for (const ae in server_data) {
                const ae_data = server_data[ae];
                const ae_rowspan = server_data[ae]['links'].length;
                let first_in_ae = true;
                for (const link in ae_data['links']) {
                    // console.log(`ae: ${ae} ae_data: ${ae_data} link: ${link}`);
                    const row = table.insertRow(-1);
                    const link_data = ae_data['links'][link]
                    const line_counter = table.rows.length -1;

                    row.insertCell(-1).innerHTML = line_counter;

                    if (server_rowspan > 1) {
                        if (first_in_server) {
                            const label_cell = row.insertCell(-1);
                            label_cell.innerHTML = server;
                            label_cell.setAttribute('rowspan', server_rowspan);
                            const new_label_cell = row.insertCell(-1);
                            new_label_cell.innerHTML = '';
                            new_label_cell.setAttribute('rowspan', server_rowspan);
                            first_in_server = false;
                        }
                    } else {
                        row.insertCell(-1).innerHTML = server;
                        row.insertCell(-1).innerHTML = '';
                    }

                    if (ae_rowspan > 1) {
                        if (first_in_ae) {
                            const ae_cell = row.insertCell(-1);
                            ae_cell.innerHTML = ae;
                            ae_cell.setAttribute('rowspan', ae_rowspan);
                            const cts_cell = row.insertCell(-1);
                            cts_cell.innerHTML = '';
                            cts_cell.setAttribute('rowspan', ae_rowspan);
                            first_in_ae = false;
                            const speed_cell = row.insertCell(-1);
                            speed_cell.innerHTML = ae_data['speed'];
                            speed_cell.setAttribute('rowspan', ae_rowspan);
                            first_in_ae = false;
                        }
                    } else {
                        row.insertCell(-1).innerHTML = ae;
                        row.insertCell(-1).innerHTML = '';
                        row.insertCell(-1).innerHTML = ae_data['speed'];
                    }

                    row.insertCell(-1).innerHTML = link_data.server_intf;
                    row.insertCell(-1).innerHTML = link_data.switch;
                    row.insertCell(-1).innerHTML = link_data.switch_intf;

                }

            }
        }
            
        this.shadowRoot.getElementById("num_links").innerHTML = table.rows.length -1;
        this.shadowRoot.getElementById("gs-header").innerHTML = `${gs_count} Generic Systems, ${table.rows.length -1} Links`;
    }
}
customElements.define("generic-systems", GenericSystems);
