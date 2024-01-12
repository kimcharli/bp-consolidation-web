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
            stroke-opacity: 1;
            stroke: black;
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
        .interface-name[data-state="loaded"] {
            fill: green;
            stroke: #0000FF;
        }
        svg#leaf-gs-box[data-state="loaded"] {
            fill: green;
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
        @keyframes pulse {
            0%, 49% {
              color: white;
            }
            50%, 100% {
              color: transparent;
            }
        }
    
        .data-set[data-state="init"] {
            background-color: var(--global-warning-color);
            fill: var(--global-warning-color);
        }
        .data-set[data-state="loading"] {
            animation: pulse 1s infinite
        }
        .data-set[data-state="loaded"] {
            background-color: var(--global-ok-color);
            fill: var(--global-ok-color);
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
        
            <use id="leaf1-box" x="0" y="0" href="#leaf" class="data-set" data-state="init" />
            <text id="leaf1-label" x="50" y="12" text-anchor="middle" alignment-baseline="central" class="data-set" data-state="init">leaf1</text>
        
            <use id="leaf2-box" x="110" y="0" href="#leaf" class="data-set" data-state="init"/>
            <text id="leaf2-label" x="160" y="12" text-anchor="middle" alignment-baseline="central">leaf2</text>

            <use id="access-gs-box" x="0" y="50" href="#access-gs" class="data-set" data-state="init" />
            <text id="access-gs-label" x="100" y="62" text-anchor="middle" alignment-baseline="central">access-gs</text>

            <use id="access1-box" x="0" y="50" href="#access" visibility="hidden" class="data-set" data-state="init" />
            <text id="access1-label" x="50" y="62" text-anchor="middle" alignment-baseline="central" visibility="hidden">access1</text>
        
            <use id="access2-box" x="110" y="50" href="#access" visibility="hidden" class="data-set" data-state="init" />
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
            
                <use id="leaf-gs-box" x="0" y="0" href="#leaf-gs" class="data-set" data-state="init"/>
                <text id="leaf-gs-label" x="100" y="12" text-anchor="middle" alignment-baseline="central">leaf-gs</text>
            
                <use id="tor1-box" x="0" y="50" href="#access" class="data-set" data-state="init" />
                <text id="tor1-label" x="50" y="62" text-anchor="middle" alignment-baseline="central">leaf1</text>
            
                <use id="tor2-box" x="110" y="50" href="#access" class="data-set" data-state="init"/>
                <text id="tor2-label" x="160" y="62" text-anchor="middle" alignment-baseline="central">leaf2</text>
            
                <line x1="30" y1="25" x2="30" y2="50" />
                <line x1="60" y1="25" x2="140" y2="50" />
                <line x1="140" y1="25" x2="60" y2="50" />
                <line x1="170" y1="25" x2="170" y2="50" />
                <line x1="90" y1="62" x2="110" y2="62" />

                <text id="leafgs1-intf1" class="interface-name" x="25" y="22">et-0/0/20</text>
                <text id="leafgs1-intf2" class="interface-name" x="65" y="22">et-0/0/21</text>
                <text id="leafgs2-intf1" class="interface-name" x="135" y="22">et-0/0/20</text>
                <text id="leafgs2-intf2" class="interface-name" x="175" y="22">et-0/0/21</text>
    
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
                window.dispatchEvent(
                    new CustomEvent(GlobalEventEnum.CONNECT_SUCCESS, { detail: { name: element }})
                );                                
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

    load_id_element(id, value) {
        this.shadowRoot.getElementById(id).innerHTML = value;
        this.shadowRoot.getElementById(id).dataset.state = "loaded";
        this.shadowRoot.getElementById(id).style.fill = "red";
    }

    handleSyncState(event) {
        // tor_bp side
        this.load_id_element("tor1-label", globalData.access_switches[0][0]);
        this.shadowRoot.getElementById('tor1-box').dataset.state = "loaded";
        this.load_id_element("tor2-label", globalData.access_switches[1][0]);
        this.shadowRoot.getElementById('tor2-box').dataset.state = "loaded";
        this.load_id_element("leaf-gs-label", globalData.leaf_gs.label);
        this.shadowRoot.getElementById('leaf-gs-box').dataset.state = "loaded";
        this.load_id_element("leafgs1-intf1", globalData.leaf_gs.intfs[0]);
        this.load_id_element("leafgs1-intf2", globalData.leaf_gs.intfs[2]);
        this.load_id_element("leafgs2-intf1", globalData.leaf_gs.intfs[1]);
        this.load_id_element("leafgs2-intf2", globalData.leaf_gs.intfs[3]);

        // main_bp side
        this.load_id_element("leaf1-intf1", globalData.leaf_gs.intfs[0]);
        this.load_id_element("leaf1-intf2", globalData.leaf_gs.intfs[2]);
        this.load_id_element("leaf2-intf1", globalData.leaf_gs.intfs[1]);
        this.load_id_element("leaf2-intf2", globalData.leaf_gs.intfs[3]);

        if (globalData.tor_gs.id && globalData.tor_gs.ae_id) {
            // tor_gs exists in the main_bp
            this.load_id_element("access-gs-label", globalData.tor_gs.label);
            this.shadowRoot.getElementById('access-gs-box').dataset.state = "loaded";    
            this.load_id_element("leaf1-label", globalData.leaf_switches[0][0]);
            this.shadowRoot.getElementById("leaf1-box").dataset.state = "loaded";
            this.load_id_element("leaf2-label", globalData.leaf_switches[1][0]);
            this.shadowRoot.getElementById("leaf2-box").dataset.state = "loaded";
        } else if (globalData.leaf_switches[0][1].id && globalData.leaf_switches[1][1].id) {
            this.load_id_element("leaf1-label", globalData.leaf_switches[0][0]);
            this.shadowRoot.getElementById("leaf1-box").dataset.state = "loaded";
            this.load_id_element("leaf2-label", globalData.leaf_switches[1][0]);
            this.shadowRoot.getElementById("leaf2-box").dataset.state = "loaded";
            this.shadowRoot.getElementById("access-gs-box").style.visibility = "hidden";
            this.shadowRoot.getElementById("access-gs-label").style.visibility = "hidden";
            this.shadowRoot.getElementById("access1-box").style.visibility = "visible";
            this.shadowRoot.getElementById("access1-box").dataset.state = "loaded";
            this.shadowRoot.getElementById("access1-label").style.visibility = "visible";
            this.shadowRoot.getElementById("access2-box").dataset.state = "loaded";
            this.shadowRoot.getElementById("access2-box").style.visibility = "visible";
            this.shadowRoot.getElementById("access2-label").style.visibility = "visible";
            this.load_id_element("access1-label", globalData.access_switches[0][0]);
            this.load_id_element("access2-label", globalData.access_switches[1][0]);
            }

    }
}
customElements.define("access-switches", AccessSwitches);
