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
        tr {
            background-color: var(--top-header-color);
        }
        th {
            text-align: left;
            background-color: #0096a4;
            border: 1px solid;
        }
        .no-border {
            border: 0;
        }

        td {
            text-align: left;
            border: 1px solid;
        }
        .btn {
            fill: #fff;
        }
        button {
            // border-radius: 100%;
            width: 35px;
            height: 35px;
            background-size:cover;
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

        /* Tooltip container */
        .tooltip-container {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
        }

        .tooltip-object {
            // background-color: yellow;
            // color: orange;
            border: none;
            // padding: 10px 20px;
            cursor: pointer;
            border-radius: 5px;
        }

        .tooltip-text {
            visibility: hidden;
            width: 150px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 5px;
            padding: 5px;
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
          }

        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        @keyframes pulse {
            0%, 49% {
              color: white;
            }
            50%, 100% {
              color: transparent;
            }
        }

        #connect-button {
            // background-color: #ffb71b;
            background-color: var(--warning-color);
        }
    </style>

    <table class="no-border">
        <tr class="no-border">
            <td class="no-border" style="width: 100%;">
                <a href="/"><img style="object-position: left top;" src="/images/home.svg" alt="Home" width="30" height="30"></a>
                <a href="/graphql" target="_blank"><img src="/images/graphql.svg" alt="graphql" width="30" height="30"></a>
                <a href="/css/style.css"><img src="/images/css-3.svg" alt="style.css" width="30" height="30"></a>
            </td>
            <td class="no-border">
                <table>
                    <tr>
                        <td class="tooltip-container">
                            <button id="connect-button" type="submit" class="tooltip-object">off</button>
                            <span class="tooltip-text">Click to Connect</span>
                        </td>
                        <th>server</th>
                        <th>port</th>
                        <th>username</th>
                        <th>password</th>
                    </tr>
                    <tr>
                        <td class="tooltip-container">
                            <button id="edit-button" type="submit" class="tooltip-object">Edit</button>
                            <span class="tooltip-text">Click to Edit</span>
                        </td>
                        <td><input id="apstra-host" name="apstra-host" /></th>
                        <td><input id="apstra-port" type="number" name="apstra-port" /></th>
                        <td><input id="apstra-username" name="apstra-username" /></th>
                        <td><input id="apstra-password" type="password" name="apstra-password"  /></th>
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
        const connectButton = this.shadowRoot.getElementById('connect-button');
        connectButton.addEventListener('click', this.handleConnectClick.bind(this));
        const editButton = this.shadowRoot.getElementById('edit-button');
        editButton.addEventListener('click', this.handleEditClick.bind(this));
    }

    connectedCallback() {
        this.get_initial_server();
    }

    async get_initial_server() {
        console.log('server fetch started');
        const server_query = {
            'query': "{\n  server {\n    host\n    port\n    username\n    password\n  }\n  \n}"
        }
        const response = await fetch('/graphql', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/graphql-response+json' 
            },
            body: JSON.stringify(server_query)
        });
        const data = await response.json();

        console.log('get_initial_server response: ' + data);

        this.shadowRoot.getElementById('apstra-host').value = data.data.server.host;
        this.shadowRoot.getElementById('apstra-port').value = data.data.server.port;
        this.shadowRoot.getElementById('apstra-username').value = data.data.server.username;
        this.shadowRoot.getElementById('apstra-password').value = data.data.server.password;
        console.log('server fetch ended');
        return
    }

    async connect_server(apstra_host, apstra_port, apstra_username, apstra_password) {
        console.log('login_server', apstra_host, apstra_port, apstra_username, apstra_password);
        const server_query = {
            'query': "mutation {\n  loginServer(host: \"" + apstra_host + "\", port: " + apstra_port + ", username: \"" + apstra_username + "\", password: \"" + apstra_password + "\") {\n    host\n  }\n}",
            'variables': {
                'host': apstra_host,
                'port': apstra_port,
                'username': apstra_username,
                'password': apstra_password
            }
        };
        const response = await fetch('/graphql', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/graphql-response+json' 
            },
            body: JSON.stringify(server_query)
        })
            .then(response => response.json())
            .then(data => {console.log(data)})
            .catch(error => console.log('Error:', error));
        return response;
    }

    handleConnectClick(event) {
        if (event.target.innerHTML === 'off') {
            event.target.innerHTML = 'on';
            const apstra_host = this.shadowRoot.getElementById('apstra-host').value;
            const apstra_port = this.shadowRoot.getElementById('apstra-port').value;
            const apstra_username = this.shadowRoot.getElementById('apstra-username').value;
            const apstra_password = this.shadowRoot.getElementById('apstra-password').value;
            this.connect_server(apstra_host, apstra_port, apstra_username, apstra_password);
            event.target.style.backgroundColor = 'var(--normal-color)';
            event.target.style.animation = 'pulse 1s infinite';
        } else if (event.target.innerHTML === 'on') {
            event.target.innerHTML  = 'off';
            event.target.style.backgroundColor = 'var(--warning-color)';
            event.target.style.animation = '';
        }
    }

    handleEditClick(event) {
        alert('handleEditClicked');
    }   
    // render() {
    //     return html`
    //         <p>Welcome to the Lit tutorial!</p>
    //         <p>This is the ${this.version} code.</p>
    //     `;
    // }
}   
customElements.define('apstra-server', ApstraServer);