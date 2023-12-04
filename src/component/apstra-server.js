const template = document.createElement("template");
template.innerHTML = `
    <style>
        p {
            color: blue;
        }
        table {
            border-collapse: collapse;
            border: 1px solid;
        }
        th {
            text-align: left;
            background-color: coral;
            border: 1px solid;
        }
        .no-border {
            border: 0;
        }
        td {
            text-align: left;
            border: 1px solid;
        }
        button {
            background: url(static/images/login-blue.svg) no-repeat;
        }
    </style>

    <input type="color" name="color" id="color" />
    <input type="datetime-local" name="datetime" id="datetime" />
    <table class="no-border">
        <tr class="no-border">
            <td class="no-border">
                <table>
                    <tr>
                        <th>server</th>
                        <th>port</th>
                        <th>username</th>
                        <th>password</th>
                    </tr>
                    <tr>
                        <td><input name="apstra-host" value="10.85.192.50" /></th>
                        <td><input type="number" name="apstra-port" value="443" /></th>
                        <td><input name="apstra-username" value="admin" /></th>
                        <td><input type="password" name="apstra-password" value="password" /></th>
                    </tr>
                </table>
            </td>
            <td class="no-border"><button id="connect"><img src="/static/images/login-blue.svg" width="30" height="30" /></button></td>
        </tr>
    </table

</div>

`


class ApstraServer extends HTMLElement {

    
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }

    // render() {
    //     return html`
    //         <p>Welcome to the Lit tutorial!</p>
    //         <p>This is the ${this.version} code.</p>
    //     `;
    // }
}   
customElements.define('apstra-server', ApstraServer);