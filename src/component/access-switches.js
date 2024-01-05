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
        th {
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

    <table>
    <tr>
        <th>Main Blueprint</th>
        <th>ToR Blueprint</th>
    </tr>
    <tr>
        <td id="main_bp" class="blueprint" data-id>M</td>
        <td id="tor_bp" class="blueprint" data-id>T</td>
    </tr>
    <tr>
        <td>
            <svg viewBox="0 0 200 75" width="400px" xmlns="http://www.w3.org/2000/svg">
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
            <text id="access-gs-label" x="100" y="62" text-anchor="middle" alignment-baseline="central">access-gs</text>

            <use x="0" y="50" href="#access" visibility="hidden" />
            <text id="access1-label" x="50" y="62" text-anchor="middle" alignment-baseline="central" visibility="hidden">access1</text>
        
            <use x="110" y="50" href="#access" visibility="hidden" />
            <text id="access2-label" x="160" y="62" text-anchor="middle" alignment-baseline="central" visibility="hidden">access2</text>

            <line x1="30" y1="25" x2="30" y2="50" />
            <line x1="60" y1="25" x2="140" y2="50" />
            <line x1="140" y1="25" x2="60" y2="50" />
            <line x1="170" y1="25" x2="170" y2="50" />
            <line x1="90" y1="62" x2="110" y2="62" visibility="hidden" />
            <text class="interface-name" x="100" y="60" visibility="hidden">et-0/0/53</text>

            <text id="leaf1-intf1" class="interface-name" x="25" y="22">et-0/0/20</text>
            <text id="leaf1-intf2" class="interface-name" x="65" y="22">et-0/0/21</text>
            <text id="leaf2-intf1" class="interface-name" x="135" y="22">et-0/0/20</text>
            <text id="leaf2-intf2" class="interface-name" x="175" y="22">et-0/0/21</text>

            <text id="access1-intf1" class="interface-name" x="25" y="53">et-0/0/48</text>
            <text id="access1-intf2" class="interface-name" x="65" y="53">et-0/0/49</text>
            <text id="access2-intf1" class="interface-name" x="135" y="53">et-0/0/48</text>
            <text id="access2-intf2" class="interface-name" x="175" y="53">et-0/0/49</text>

            </svg>

        </th>
        <td>
            <svg viewBox="0 0 200 75" width="400px" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <rect id="access" width="90" height="25" ry="5" />
                    <rect id="leaf-gs" width="200" height="25" ry="5" />
                </defs>
            
                <use x="0" y="0" href="#leaf-gs" />
                <text id="leaf-gs-label" x="100" y="12" text-anchor="middle" alignment-baseline="central">leaf-gs</text>
            
                <use x="0" y="50" href="#access" />
                <text id="tor1-label" x="50" y="62" text-anchor="middle" alignment-baseline="central">leaf1</text>
            
                <use x="110" y="50" href="#access" />
                <text id="tor2-label" x="160" y="62" text-anchor="middle" alignment-baseline="central">leaf2</text>
            
                <line x1="30" y1="25" x2="30" y2="50" />
                <line x1="60" y1="25" x2="140" y2="50" />
                <line x1="140" y1="25" x2="60" y2="50" />
                <line x1="170" y1="25" x2="170" y2="50" />
                <line x1="90" y1="62" x2="110" y2="62" />

                <text id="leaf1-intf1" class="interface-name" x="25" y="22">et-0/0/20</text>
                <text id="leaf1-intf2" class="interface-name" x="65" y="22">et-0/0/21</text>
                <text id="leaf2-intf1" class="interface-name" x="135" y="22">et-0/0/20</text>
                <text id="leaf2-intf2" class="interface-name" x="165" y="22">et-0/0/21</text>
    
                <text class="interface-name" x="100" y="60">et-0/0/53</text>

                <text id="access1-intf1" class="interface-name" x="25" y="53">et-0/0/48</text>
                <text id="access1-intf2" class="interface-name" x="65" y="53">et-0/0/49</text>
                <text id="access2-intf1" class="interface-name" x="135" y="53">et-0/0/48</text>
                <text id="access2-intf2" class="interface-name" x="175" y="53">et-0/0/49</text>
    
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

        window.addEventListener(GlobalEventEnum.FETCH_ENV_INI, this.handleFetchEnvIni.bind(this));
        window.addEventListener(GlobalEventEnum.CLEAR_ENV_INI, this.handleClearEnvIni.bind(this));
        window.addEventListener(GlobalEventEnum.CONNECT_BLUEPRINT, this.blueprintConnectRequested.bind(this));
        window.addEventListener(GlobalEventEnum.SYNC_STATE, this.handleSyncState.bind(this));
    }

    handleFetchEnvIni(event) {
        const data = event.detail
        console.log('AccessSwitches: handleFetchEnvIni', data);
        this.shadowRoot.getElementById("main_bp").innerHTML = data.main_bp_label;
        this.shadowRoot.getElementById("tor_bp").innerHTML = data.tor_bp_label;
    }

    handleClearEnvIni(event) {
        console.log('AccessSwitches: handleClearEnvIni');
        this.shadowRoot.getElementById("main_bp").innerHTML = 'M';
        this.shadowRoot.getElementById("main_bp").dataset.id = '';
        this.shadowRoot.getElementById("tor_bp").innerHTML = 'T';
        this.shadowRoot.getElementById("tor_bp").dataset.id = '';
    }

    connectedCallback() {
        // this.fetch_blueprint();
        // this.shadowRoot.getElementById("access-gs-label").innerHTML = "atl1tor-r4r16";
        // this.shadowRoot.getElementById("leaf1-label").innerHTML = "atl1lef15-r5r13";
        // this.shadowRoot.getElementById("leaf2-label").innerHTML = "atl1lef16-r5r14";
        // this.shadowRoot.getElementById("leaf-gs-label").innerHTML = "UPLINK-LEF-15-16-r4r16";
        // this.shadowRoot.getElementById("access1-label").innerHTML = "atl1tor-r4r16a";
        // this.shadowRoot.getElementById("access2-label").innerHTML = "atl1tor-r4r16b";
        // this.shadowRoot.getElementById("leaf1-intf1").innerHTML = "et-0/0/20";
        // this.shadowRoot.getElementById("leaf1-intf2").innerHTML = "et-0/0/21";
        // this.shadowRoot.getElementById("leaf2-intf1").innerHTML = "et-0/0/20";
        // this.shadowRoot.getElementById("leaf2-intf2").innerHTML = "et-0/0/21";
        // this.shadowRoot.getElementById("access1-intf1").innerHTML = "et-0/0/48";
        // this.shadowRoot.getElementById("access1-intf2").innerHTML = "et-0/0/49";
        // this.shadowRoot.getElementById("access2-intf1").innerHTML = "et-0/0/48";
        // this.shadowRoot.getElementById("access2-intf2").innerHTML = "et-0/0/49";
    }

    connect_blueprint() {
        ['main_bp', 'tor_bp'].forEach(element => 
            fetch('/login-blueprint', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label: this.shadowRoot.getElementById(element).innerHTML,
                    role: element,
                })
            })
            .then(result => {
                if(!result.ok) {
                    return result.text().then(text => { throw new Error(text) });
                }
                else {
                    return result.json();
                }
            })
            .then(data => {
                console.log(`connect_blueprint then`, data)
                this.shadowRoot.getElementById(element).dataset.id = data.id;
                this.shadowRoot.getElementById(element).innerHTML = `<a href="${data.url}" target="_blank">${data.label}</a>`;
            })
        )

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

    handleSyncState(event) {
        // console.log('handleSyncState - globalData:', globalData, globalData.switches[0])
        this.shadowRoot.getElementById("tor1-label").innerHTML = globalData.switches[0]
        this.shadowRoot.getElementById("access1-label").innerHTML = globalData.switches[0]
        this.shadowRoot.getElementById("tor2-label").innerHTML = globalData.switches[1]
        this.shadowRoot.getElementById("access2-label").innerHTML = globalData.switches[1]

    }
}
customElements.define("access-switches", AccessSwitches);
