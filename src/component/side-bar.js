import { GlobalEventEnum } from "./common.js";

const template = document.createElement("template");
template.innerHTML = `
    <style>
    div {
        background: green;
        width: 180px;
        hight: max-content;
    }
    button {
        background-color: var(--global-warning-color);
        text-align: left;
        // border: none;
        // color: white;
        // padding: 15px 32px;
        // text-align: left;
        // text-decoration: none;
        // display: block;
        // font-size: 16px;
        width: 100%;
    }
    img {
        width: 20px;
        height: 20px;
        background-color: white;
    }
    #load-env-div {
        font-family: Arial, Helvetica, sans-serif;
    }
    #load-env-div[data-loaded=""] {
        background-color: var(--global-warning-color);
    }
    #load-env-div[data-loaded="loaded"] {
        background-color: var(--global-ok-color);
    }

    </style>
    <h3>Steps</h3>
    <div>
        <div id="load-env-div" data-loaded>
            Load environment <a href="/static/env-example.ini" download="env-example.ini"><img src="/images/download.svg" /></a>
            <img id="upload-env-ini-img" src="/images/upload.svg" alt="Upload ini" /><input type="file" id="upload-env-ini-input" style="display: none;">
        </div>
        <div>
            <button id="connect-button" type="button">Connect</button>
        </div>
        <div>
            <button id="sync-state" type="button">Sync States</button>
        </div>
        <div>
            <button type="button">Migrate Access Switches</button>
        </div>
        <div>
            <button type="button">Migrate Access Switches</button>
        </div>
        <div>
            <button type="button">Migrate Generic Systems</button>
        </div>
        <div>
            <button type="button">Migrate Virtual Networks</button>
        </div>
        <div>
            <button type="button">Migrate CTs</button>
        </div>
        <div>
            <button type="button">Pull Configurations</button>
        </div>
        <div>
            <button type="button">Move Devices</button>
        </div>
    </div>
`

class SideBar extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
        const uploadImage = this.shadowRoot.getElementById('upload-env-ini-img');
        uploadImage.addEventListener('click', this.handleUploadIniImageClick.bind(this));
        const uploadInput = this.shadowRoot.getElementById('upload-env-ini-input');
        uploadInput.addEventListener('change', this.handleUploadIniInputChange.bind(this));

        const connectButton = this.shadowRoot.getElementById('connect-button');
        connectButton.addEventListener('click', this.handleConnectClick.bind(this));

        const syncStateButton = this.shadowRoot.getElementById('sync-state');
        syncStateButton.addEventListener('click', this.handleSyncStateClick.bind(this));

        window.addEventListener(GlobalEventEnum.CONNECT_SUCCESS, this.connectServerSuccess.bind(this));
        window.addEventListener(GlobalEventEnum.CONNECT_LOGOUT, this.connectServerLogout.bind(this));

    }

    handleUploadIniImageClick(event) {
        console.log('upload ini image clicked');
        this.shadowRoot.getElementById('upload-env-ini-input').click();
    }

    handleUploadIniInputChange(event) {
        const input_element = this.shadowRoot.getElementById('upload-env-ini-input');
        const formData = new FormData();
        formData.append('file', input_element.files[0]);
        fetch('/upload-env-ini', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            this.shadowRoot.getElementById('load-env-div').dataset.loaded = 'loaded';
            window.dispatchEvent(
                new CustomEvent(GlobalEventEnum.FETCH_ENV_INI )
            );

        })
        .catch(error => console.error('Error:', error));
    }

    handleConnectClick(event) {
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.CONNECT_REQUEST, { bubbles: true, composed: true } )
        );

    }

    connectServerSuccess(event) {
        this.shadowRoot.getElementById('connect-button').style.backgroundColor = 'var(--global-ok-color)';
    }

    connectServerLogout(event) {
        this.shadowRoot.getElementById('connect-button').style.backgroundColor = 'var(--global-warning-color)';
    }

    handleSyncStateClick(event) {
        window.dispatchEvent(
            new CustomEvent(GlobalEventEnum.SYNC_STATE_REQUEST, { bubbles: true, composed: true } )
        );
    }

}   
customElements.define('side-bar', SideBar);