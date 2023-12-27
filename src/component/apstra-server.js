import { queryFetch, GlobalEventEnum } from "./common.js";

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
            background-color: var(--global-header-color);
        }
        th {
            text-align: left;
            background-color: var(--global-th-color);
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
            z-index: 10;  /* bring it on top */
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
            background-color: var(--global-warning-color);
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
                            <span id="connect-button-tooltip-text" class="tooltip-text">Click to Connect</span>
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
                        <td><input id="apstra-host" readonly></th>
                        <td><input id="apstra-port" readonly></th>
                        <td><input id="apstra-username" readonly></th>
                        <td><input id="apstra-password" type="password" readonly /></th>
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

        this.shadowRoot.getElementById('edit-button').addEventListener('click', this.handleEditClick.bind(this));

        window.addEventListener(GlobalEventEnum.CONNECT_REQUEST, this.connectServer.bind(this));
        window.addEventListener(GlobalEventEnum.FETCH_ENV_INI, this.fetchEnvIni.bind(this));
    }

    connectedCallback() {
        // this.fetch_server();
    }

    fetchEnvIni(event){
        this.fetch_server();
        console.log('apstar-server.js:fetchEnvIni(): fetch server done');
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.FETCH_BP_REQUEST )
        );

    }

    async fetch_server() {
        queryFetch(`
          {
            fetchServer {
              id
              host
              port
              username
              password
            }
          }  
        `)
        .then(data => {
            this.shadowRoot.getElementById('apstra-host').value = data.data.fetchServer.host;
            this.shadowRoot.getElementById('apstra-port').value = data.data.fetchServer.port;
            this.shadowRoot.getElementById('apstra-username').value = data.data.fetchServer.username;
            this.shadowRoot.getElementById('apstra-password').value = data.data.fetchServer.password;
        })

    }


    login_server(apstra_host, apstra_port, apstra_username, apstra_password) {
        const login_promise = new Promise((resolve, reject) => {
            if (apstra_host === '' || apstra_port === '' || apstra_username === '' || apstra_password === '') {
                const error_message = 'the server, port, username, and password must be filled in to proceed. Load environment.'
                alert(error_message);
                reject(error_message);
            };
            queryFetch(`
                mutation LoginServer($host: String!, $port: Int!, $username: String!, $password: String!){
                    loginServer(host: $host, port: $port, username: $username, password: $password) {
                        __typename
                        ... on ApstraServerSuccess {
                            host
                        }
                        ... on ApstraServerLoginFail {
                            server
                            error
                        }
                    }
                }
            `, { host: apstra_host, port: parseInt(apstra_port), username: apstra_username, password: apstra_password })
            .then(data => {
                if (data.errors) {
                    reject(data.errors);
                } else {
                    resolve(data);
                }})
            .catch(error => reject(error));
        })
    }

    async logout_server() {
        return queryFetch(`
            mutation {
                logoutServer {
                    host
                }
            }
        `)
        .then(data => { return data})
    }

    connectServer(event) {
        const thisTarget = this.shadowRoot.getElementById('connect-button')
        const tooltipText = this.shadowRoot.getElementById('connect-button-tooltip-text');
        const apstra_host = this.shadowRoot.getElementById('apstra-host').value;
        const apstra_port = this.shadowRoot.getElementById('apstra-port').value;
        const apstra_username = this.shadowRoot.getElementById('apstra-username').value;
        const apstra_password = this.shadowRoot.getElementById('apstra-password').value;
        this.login_server(apstra_host, apstra_port, apstra_username, apstra_password)
            .then(data => {
                console.log(data);
                switch(data.data.loginServer.__typename) {
                    case 'ApstraServerSuccess':
                        window.dispatchEvent(
                            new CustomEvent('global-connect-success')
                        );                
                        thisTarget.innerHTML = 'on';
                        thisTarget.style.backgroundColor = 'var(--global-ok-color)';
                        thisTarget.style.animation = 'pulse 1s infinite';
                        tooltipText.innerHTML = 'Click to Disconnect';  
                        break;
                    case 'ApstraServerLoginFail':
                        thisTarget.innerHTML  = 'fail';
                        thisTarget.style.backgroundColor = 'var(--global-error-color)';
                        thisTarget.style.animation = 'pulse 1s infinite';
                        tooltipText.innerHTML = 'Click to Disconnect';            
                    break;
                }
                window.dispatchEvent(
                    new CustomEvent(GlobalEventEnum.BP_CONNECT_REQUEST)
                );
            })
            .catch(error => {
                console.log(error);
            })

    }

    handleConnectClick(event) {
        const thisTarget = event.target;
        const tooltipText = this.shadowRoot.getElementById('connect-button-tooltip-text');
        switch(event.target.innerHTML) {
            case 'off':
                this.connectServer(event);
                break;
            case 'on':
            case 'fail':
                window.dispatchEvent(
                    new CustomEvent('global-connect-logout')
                );                
                thisTarget.innerHTML  = 'off';
                thisTarget.style.backgroundColor = 'var(--global-warning-color)';
                thisTarget.style.animation = '';
                this.logout_server()
                tooltipText.innerHTML = 'Click to Connect';
                break;
        }
    }

    handleEditClick(event) {
        alert('handleEditClicked');
    }   
}   
customElements.define('apstra-server', ApstraServer);