import { GlobalEventEnum, globalData, CkIDB } from "./common.js";

const template = document.createElement("template");
template.innerHTML = `
    <style>
        .th {
            background-color: var(--global-th-color);
        }

        .vn[data-state="init"] {
            background-color: var(--global-warning-color);
        }
    </style>

    <div id="vn-total" class="th" data-vns>Virtual Networks</div>
    <div id="vns"></div>    
    </table>
`

class VirtualNetworks extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        window.addEventListener(GlobalEventEnum.SYNC_STATE, this.handleSyncState.bind(this));

    }


    handleSyncState(event) {
        const vns_div = this.shadowRoot.getElementById("vns");
        for (const i in globalData.vnis) {
            const vni = globalData.vnis[i];
            // console.log('vni', vni)            
            const vn_span = document.createElement("button");
            vn_span.setAttribute('id', 'vn-' + vni);
            vn_span.setAttribute('class', 'vn');
            vn_span.dataset.state = 'init';
            vn_span.appendChild(document.createTextNode(vni));
            vns_div.append(vn_span);
        }
        const vns_total = this.shadowRoot.getElementById("vn-total");
        vns_total.dataset.vns = globalData.vnis.length;
        vns_total.innerHTML =  `Virtual Networks (${globalData.vnis.length})`;
    }
}
customElements.define("virtual-networks", VirtualNetworks);
