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
        <td>Masin</th>
        <td>AZ</th>
    </tr>
    <tr>
        <td>box</th>
        <td>box</th>
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