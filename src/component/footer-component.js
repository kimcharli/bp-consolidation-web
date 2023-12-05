const template = document.createElement('template');
template.innerHTML = `
    <style>
        h3 {
            color: orange;
        }
    </style>
    <h3>footer</h3>
`

class FooterComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }
}

customElements.define('footer-component', FooterComponent);
