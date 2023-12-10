import { queryFetch } from "./common.js";

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
    </style>

    <table>
    <tr>
        <th>Main Blueprint</th>
        <th>ToR Blueprint</th>
    </tr>
    <tr>
        <td id="main_bp">Masin</th>
        <td id="tor_bp">AZ</th>
    </tr>
    <tr>
        <td>box</th>
        <td>
            <svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <rect id="leaf" width="50" height="25" ry="5" style="fill:transparent;stroke-width:1;stroke:black" />
                    <rect id="leaf-gs" width="110" height="25" ry="5" style="fill:transparent;stroke-width:1;stroke:black" />
                </defs>
            
                <use x="0" y="0" href="#leaf-gs" />
                <text x="55" y="12" text-anchor="middle" alignment-baseline="central">leaf-gs</text>
            
                <use x="0" y="50" href="#leaf" />
                <text x="25" y="62" text-anchor="middle" alignment-baseline="central">leaf1</text>
            
                <use x="60" y="50" href="#leaf" />
                <text x="85" y="62" text-anchor="middle" alignment-baseline="central">leaf2</text>
            
                <line x1="20" y1="25" x2="15" y2="50" style="stroke:black;stroke-width:1" />
                <line x1="40" y1="25" x2="75" y2="50" style="stroke:black;stroke-width:1" />
                <line x1="60" y1="25" x2="35" y2="50" style="stroke:black;stroke-width:1" />
                <line x1="80" y1="25" x2="95" y2="50" style="stroke:black;stroke-width:1" />
                <line x1="50" y1="62" x2="60" y2="62" style="stroke:black;stroke-width:1" />
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

        // this.shadowRoot.querySelector("button").addEventListener("click", () => {
        //     this.dispatchEvent(new CustomEvent("onEdit", { detail: this.accessSwitch }));
        // });
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
                this.shadowRoot.getElementById(element.role).style.backgroundColor = 'var(--global-warning-color)';
            })
        });
    }

    connectedCallback() {
        this.fetch_blueprint();
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
}
customElements.define("access-switches", AccessSwitches);