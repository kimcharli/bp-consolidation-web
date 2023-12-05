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
            border-radius: 100%;
        }
        .btn {
            fill: #fff;
        }
        .btn {
            text-decoration: none; 
            border: none; 
            font-size: 16px; 
            border-radius: 5px; 
            box-shadow: 3px 2px 22px 1px rgba(0, 0, 0, 0.24); 
            cursor: pointer; 
            outline: none; 
            transition: 0.2s all;             
        }
        .btn:active {
            transform: scale(0.98);
            box-shadow: 0 0 0 3px #e78267;
        }
    </style>

    <input type="color" name="color" id="color" />
    <input type="datetime-local" name="datetime" id="datetime" />
    <table class="no-border">
        <tr class="no-border">
            <td class="no-border">
                <image class="btn" src="/static/images/powered-on.svg" width="35" height="35" />
                <image class="btn" src="/static/images/powered-off.svg" width="35" height="35" />
                <image class="btn" src="/static/images/powered-error.svg" width="35" height="35" />
            </td>
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