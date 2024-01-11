const template = document.createElement("template");
template.innerHTML = `
    <style>
    </style>
    <h3>Main Context</h3>
`

class MainContext extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }

}   
customElements.define('main-context', MainContext);