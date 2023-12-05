const template = document.createElement("template");
template.innerHTML = `
    <style>
    </style>
    <h3>SIDEBAR</h3>
`

class SideBar extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }

}   
customElements.define('side-bar', SideBar);