import { GlobalEventEnum, globalData, CkIDB, CkEnum } from "./common.js";

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
        .old-label {
            text-align: left;
            width: 32ch;
        }
        .old-label[data-state="loaded"] {
            background: var(--global-warning-color);
        }
        .new-label {
            text-align: left;
            width: 32ch;
        }
        .cts {
            text-align: right;
        }
        .speed {
            text-align: right;
        }
        .speed[data-speed="100G"] {
            background-color: #a153ba;
        }
        .speed[data-speed="40G"] {
            background-color: #896dce;
        }
        .speed[data-speed="25G"] {
            background-color: #ffb71b;
        }
        .speed[data-speed="10G"] {
            background: #037dba;
        }
        .speed[data-speed="1G"] {
            background-color: #e36b00;
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

    _ct_count(data) {
        let ct_count = data.tagged_vlans.length;
        if (data.untagged_vlan) {
            ct_count += 1;
        }
        return ct_count;
    }

    _insert_label_cell(row, server, server_rowspan) {
        const the_cell = row.insertCell(-1);
        the_cell.innerHTML = server;
        the_cell.setAttribute('rowspan', server_rowspan);
        the_cell.setAttribute('class', 'old-label');
        the_cell.dataset.id = 'gs' + server;
        the_cell.dataset.state = 'loaded';
    }

    _insert_new_label_cell(row, new_label, server_rowspan) {
        const the_cell = row.insertCell(-1);
        the_cell.innerHTML = new_label;
        the_cell.setAttribute('rowspan', server_rowspan);
        the_cell.setAttribute('class', 'new-label');
    }

    _insert_cts_cell(row, ae_data, ae_rowspan) {
        const the_cell = row.insertCell(-1);
        the_cell.innerHTML = this._ct_count(ae_data);
        the_cell.setAttribute('rowspan', ae_rowspan);
        the_cell.setAttribute('class', 'cts');
    }

    _insert_speed_cell(row, ae_data, ae_rowspan) {
        const the_cell = row.insertCell(-1);
        the_cell.innerHTML = ae_data['speed'];
        the_cell.dataset.speed = ae_data['speed'];
        the_cell.setAttribute('rowspan', ae_rowspan);
        the_cell.setAttribute('class', 'speed');
    }

    handleSyncState(event) {
        const table = this.shadowRoot.getElementById("main-table");

        const gs_count = Object.entries(globalData.servers).length;
        for (const server in globalData.servers) {
            const server_data = globalData.servers[server];
            // console.log(`handleSyncState: server=${server}, server_data`, server_data);
            let first_in_server = true;
            let server_rowspan = 0;
            for (const ae in server_data.group_links) {
                // console.log(`handleSyncState: ae=${ae}`, server_data[ae]['links']);
                server_rowspan += server_data.group_links[ae]['links'].length;
            }
            // console.log(`server: ${server} server_rowspan: ${server_rowspan}`);
            for (const ae in server_data.group_links) {
                const ae_data = server_data.group_links[ae];
                const ae_rowspan = server_data.group_links[ae]['links'].length;
                let first_in_ae = true;
                for (const link in ae_data['links']) {
                    // console.log(`ae: ${ae} ae_data: ${ae_data} link: ${link}`);
                    const row = table.insertRow(-1);
                    const link_data = ae_data['links'][link]
                    const line_counter = table.rows.length -1;

                    row.insertCell(-1).innerHTML = line_counter;

                    if (server_rowspan > 1) {
                        if (first_in_server) {
                            this._insert_label_cell(row, server, server_rowspan)
                            this._insert_new_label_cell(row, server_data.new_label, server_rowspan)
                            // const new_label_cell = row.insertCell(-1);
                            // new_label_cell.innerHTML = '';
                            // new_label_cell.setAttribute('rowspan', server_rowspan);
                            first_in_server = false;
                        }
                    } else {
                        this._insert_label_cell(row, server, server_rowspan)
                        this._insert_new_label_cell(row, server_data.new_label, server_rowspan)
                        // row.insertCell(-1).innerHTML = '';
                    }

                    if (ae_rowspan > 1) {
                        if (first_in_ae) {
                            // ae name
                            const ae_cell = row.insertCell(-1);
                            ae_cell.innerHTML = ae_data.ae_name;
                            ae_cell.setAttribute('rowspan', ae_rowspan);
                            this._insert_cts_cell(row, ae_data, ae_rowspan);
                            first_in_ae = false;
                            this._insert_speed_cell(row, ae_data, ae_rowspan);
                            first_in_ae = false;
                        }
                    } else {
                        row.insertCell(-1).innerHTML = ae_data.ae_name;
                        this._insert_cts_cell(row, ae_data, ae_rowspan)
                        this._insert_speed_cell(row, ae_data, ae_rowspan);
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
