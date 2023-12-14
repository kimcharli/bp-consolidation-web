import { queryFetch, GlobalEventEnum } from "./common.js";

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
            width: 50%;
        }
        th {
            background-color: var(--global-th-color);
        }
        svg, line, rect {
            vector-effect: non-scaling-stroke;
            fill: transparent;
            stroke: black
        }
        svg text {
            font-family: Monospace;
            font-size: 7px;
            font-weight: normal;
            text-anchor: middle;
            alignment-baseline: central;
            text-rendering: optimizeLegibility;
        }
        .interface-name {
            font-size: 5px;
            alignment-baseline: middle;
        }
        #main_bp[data-bp-id=""], #tor_bp[data-bp-id=""] {
            background-color: var(--global-warning-color);
        }
        #main_bp[data-bp-id*="-"], #tor_bp[data-bp-id*="-"] {
            background-color: var(--global-ok-color);
        }
    </style>

    <table>
    <tr>
        <th>Main Blueprint</th>
        <th>ToR Blueprint</th>
    </tr>
    <tr>
        <td id="main_bp" data-bp-label data-bp-id></th>
        <td id="tor_bp" data-bp-label data-bp-id></th>
    </tr>
    <tr>
        <td>
            <svg viewBox="0 0 200 75" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <rect id="leaf" width="90" height="25" ry="5" />
                <rect id="access-gs" width="200" height="25" ry="5" />
                <rect id="access" width="90" height="25" ry="5" />
                </defs>
        
        
            <use x="0" y="0" href="#leaf" />
            <text id="leaf1-label" x="50" y="12" text-anchor="middle" alignment-baseline="central">leaf1</text>
        
            <use x="110" y="0" href="#leaf" />
            <text id="leaf2-label" x="160" y="12" text-anchor="middle" alignment-baseline="central">leaf2</text>

            <use x="0" y="50" href="#access-gs" />
            <text id="access-gs-label" x="100" y="62" text-anchor="middle" alignment-baseline="central">leaf-gs</text>

            <line x1="30" y1="25" x2="30" y2="50" />
            <line x1="60" y1="25" x2="140" y2="50" />
            <line x1="140" y1="25" x2="60" y2="50" />
            <line x1="170" y1="25" x2="170" y2="50" />

            <text id="leaf1-intf1" class="interface-name" x="30" y="22">et-0/0/20</text>
            <text id="leaf1-intf2" class="interface-name" x="60" y="22">et-0/0/21</text>
            <text id="leaf2-intf1" class="interface-name" x="140" y="22">et-0/0/20</text>
            <text id="leaf2-intf2" class="interface-name" x="170" y="22">et-0/0/21</text>

            <text id="access1-intf1" class="interface-name" x="30" y="53">et-0/0/48</text>
            <text id="access1-intf2" class="interface-name" x="60" y="53">et-0/0/49</text>
            <text id="access2-intf1" class="interface-name" x="140" y="53">et-0/0/48</text>
            <text id="access2-intf2" class="interface-name" x="170" y="53">et-0/0/49</text>

            </svg>

        </th>
        <td>
            <svg viewBox="0 0 200 75" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <rect id="access" width="90" height="25" ry="5" />
                    <rect id="leaf-gs" width="200" height="25" ry="5" />
                </defs>
            
                <use x="0" y="0" href="#leaf-gs" />
                <text id="leaf-gs-label" x="100" y="12" text-anchor="middle" alignment-baseline="central">leaf-gs</text>
            
                <use x="0" y="50" href="#access" />
                <text id="access1-label" x="50" y="62" text-anchor="middle" alignment-baseline="central">leaf1</text>
            
                <use x="110" y="50" href="#access" />
                <text id="access2-label" x="160" y="62" text-anchor="middle" alignment-baseline="central">leaf2</text>
            
                <line x1="30" y1="25" x2="30" y2="50" />
                <line x1="60" y1="25" x2="140" y2="50" />
                <line x1="140" y1="25" x2="60" y2="50" />
                <line x1="170" y1="25" x2="170" y2="50" />
                <line x1="90" y1="62" x2="110" y2="62" />

                <text id="leaf1-intf1" class="interface-name" x="30" y="22">et-0/0/20</text>
                <text id="leaf1-intf2" class="interface-name" x="60" y="22">et-0/0/21</text>
                <text id="leaf2-intf1" class="interface-name" x="140" y="22">et-0/0/20</text>
                <text id="leaf2-intf2" class="interface-name" x="170" y="22">et-0/0/21</text>
    
                <text class="interface-name" x="100" y="60">et-0/0/53</text>

                <text id="access1-intf1" class="interface-name" x="30" y="53">et-0/0/48</text>
                <text id="access1-intf2" class="interface-name" x="60" y="53">et-0/0/49</text>
                <text id="access2-intf1" class="interface-name" x="140" y="53">et-0/0/48</text>
                <text id="access2-intf2" class="interface-name" x="170" y="53">et-0/0/49</text>
    
            </svg>
        </td>
    </tr>
    
    </table>
`

class AccessSwitches extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        window.addEventListener(GlobalEventEnum.BP_CONNECT_REQUEST, this.blueprintConnectRequested.bind(this));
        window.addEventListener(GlobalEventEnum.SYNC_STATE_REQUEST, this.syncStateRequested.bind(this));
    }

    fetch_blueprint() {
        queryFetch( `
            query {
                fetchBlueprints {                
                    label
                    role
                    id
                }
            }
        `)
        .then(data => {
            data.data.fetchBlueprints.forEach(element => {
                this.shadowRoot.getElementById(element.role).innerHTML = element.label;
                this.shadowRoot.getElementById(element.role).dataset.bpLabel = element.label;
            })
        });
    }

    connectedCallback() {
        this.fetch_blueprint();
        this.shadowRoot.getElementById("access-gs-label").innerHTML = "atl1tor-r4r16";
        this.shadowRoot.getElementById("leaf1-label").innerHTML = "atl1lef15-r5r13";
        this.shadowRoot.getElementById("leaf2-label").innerHTML = "atl1lef16-r5r14";
        this.shadowRoot.getElementById("leaf-gs-label").innerHTML = "UPLINK-LEF-15-16-r4r16";
        this.shadowRoot.getElementById("access1-label").innerHTML = "atl1tor-r4r16a";
        this.shadowRoot.getElementById("access2-label").innerHTML = "atl1tor-r4r16b";
        this.shadowRoot.getElementById("leaf1-intf1").innerHTML = "et-0/0/20";
        this.shadowRoot.getElementById("leaf1-intf2").innerHTML = "et-0/0/21";
        this.shadowRoot.getElementById("leaf2-intf1").innerHTML = "et-0/0/20";
        this.shadowRoot.getElementById("leaf2-intf2").innerHTML = "et-0/0/21";
        this.shadowRoot.getElementById("access1-intf1").innerHTML = "et-0/0/48";
        this.shadowRoot.getElementById("access1-intf2").innerHTML = "et-0/0/49";
        this.shadowRoot.getElementById("access2-intf1").innerHTML = "et-0/0/48";
        this.shadowRoot.getElementById("access2-intf2").innerHTML = "et-0/0/49";
    }

    connect_blueprint() {
        queryFetch( `
            mutation {
                connectBlueprints {                
                    label
                    role
                    id
                    bpId
                }
            }
        `)
        .then(data => {
            console.log(data);
            data.data.connectBlueprints.forEach(element => {
                this.shadowRoot.getElementById(element.role).innerHTML = element.label;
                this.shadowRoot.getElementById(element.role).dataset.bpLabel = element.label;
                this.shadowRoot.getElementById(element.role).dataset.bpId = element.bpId;
            })
        });
    }

    blueprintConnectRequested(event) {
        this.connect_blueprint();

    }

    set accessSwitch(accessSwitch) {
        this._accessSwitch = accessSwitch;
        this.render();
    }

    get accessSwitch() {
        return this._accessSwitch;
    }

    render() {
        this.shadowRoot.querySelector("td").innerHTML = this.accessSwitch.name;
    }

    // TODO: WIP
    get_gs_access(){
        queryFetch( `
            query getGenericSystems($bpRole: String!, $gsLabel: String!) {
                getGenericSystems(bpRole: $bpRole, gsLabel: $gsLabel) {
                    label
                }
            }
        `, {
            bpRole: "main_bp",
            gsLabel: this.shadowRoot.getElementById("access-gs-label").innerHTML
        })
        .then(data => {
            console.log(data);
            // data.data.connectBlueprints.forEach(element => {
            //     this.shadowRoot.getElementById(element.role).innerHTML = element.label;
            //     if (element.bpId) {
            //         this.shadowRoot.getElementById(element.role).style.backgroundColor = 'var(--global-ok-color)';
            //     }
            // })
        });
    }

    syncStateRequested(event) {
        // called by side-bar.js
        // the blueprint is already connected
        // TODO: WIP
        this.get_gs_access();
    }
}
customElements.define("access-switches", AccessSwitches);
