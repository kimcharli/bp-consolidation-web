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
        svg, line, rect {
            vector-effect: non-scaling-stroke;
            fill: transparent;
            stroke: black;
            // width: 400px;
        }
        svg text {
            font-family: system-ui, sans-serif;
            font-size: 0.5em;
            font-weight: normal;
            text-anchor: middle;
            alignment-baseline: central;
            text-rendering: optimizeLegibility;
        }
        .interface-name {
            font-size: 0.4em;
            alignment-baseline: middle;
        }
        .blueprint {
            width: 50%;
        }
        .blueprint[data-id=""] {
            background-color: var(--global-warning-color);
        }
        .blueprint[data-id*="-"] {
            background-color: var(--global-ok-color);
        }
        .center {
            text-align: center;
        }
    </style>

    <div class="th">Links</div>
    <table id="main-table">
    <tr>
        <th id="num_links">#</th>
        <th>LABEL</th>
        <th>New LABEL</th>
        <th>speed</th>
        <th>server-intf</th>
        <th>AE</th>
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

        for (const server in globalData.servers) {
        // Object.entries(globalData.servers).forEach(element => {
            const server_data = globalData.servers[server]
            console.log('server', server, server_data)
            for (const link in server_data['links']) {
                console.log('link', link, server_data['links'][link])
                const link_data = server_data['links'][link]
                const row = table.insertRow(-1);
                row.insertCell(0).innerHTML = table.rows.length -1;
                row.insertCell(1).innerHTML = server
                row.insertCell(2).innerHTML = ''
                row.insertCell(3).innerHTML = link_data.speed
                row.insertCell(4).innerHTML = link_data.server_intf
                row.insertCell(5).innerHTML = link_data.ae
                row.insertCell(6).innerHTML = link_data.switch
                row.insertCell(7).innerHTML = link_data.switch_intf
            }
            
        };
        this.shadowRoot.getElementById("num_links").innerHTML = table.rows.length -1;
    }
}
customElements.define("generic-systems", GenericSystems);
