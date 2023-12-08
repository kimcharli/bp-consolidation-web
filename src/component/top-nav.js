const template = document.createElement('template');
template.innerHTML = `
    <style>
        h3 {
            color: blue;
        }
        .navbar {
            overflow: hidden;
            background-color: #eee;
            font-family: Arial, Helvetica, sans-serif;
        }
    </style>
    <nav class="navbar">
        <div class="teal">
            <a href="/images/favicon-32x32.png">favicon</a>
            <a href="/component/apstra-server.js">apstra-server.js</a>
            <a href="/component/side-bar.js">side-bar.js</a>
            <div>
                <form hx-post='/test' hx-ext='json-enc' hx-target="#test-response-div">
                    <label>
                        Search: 
                        <input name="search" value="v1">
                    </label>
                    <label>
                        Type:
                        <input name="type" value="st1">
                    </label>
                    <input type="submit" value="Submit">            
                    <label>
                        Return Context:
                        <textarea id="test-response-div"></textarea>
                    </label>
                </form>
            </div>
        </div>
    </nav>
`

class TopNav extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.appendChild(template.content.cloneNode(true));
    }
}

customElements.define('top-nav', TopNav);
