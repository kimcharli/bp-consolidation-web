const template = document.createElement("template");
template.innerHTML = `
    <style>
    div {
        background: green;
        width: 180px;
        hight: max-content;
    }
    button {
        background-color: #424242;
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
    </style>
    <h3>Steps</h3>
    <div>
        <button type="button">Connect</button>
        <button type="button">Sync States</button>
        <button type="button">Sync States</button>
        <button type="button">Migrate Access Switches</button>
        <button type="button">Migrate Access Switches</button>
        <button type="button">Migrate Generic Systems</button>
        <button type="button">Migrate Virtual Networks</button>
        <button type="button">Migrate CTs</button>
        <button type="button">Pull Configurations</button>
        <button type="button">Move Devices</button>
    </div>
`

class SideBar extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }

}   
customElements.define('side-bar', SideBar);