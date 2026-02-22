import { React, ReactDOM } from "./deps.mjs";
import { App } from "./app.mjs";

const h = React.createElement;

ReactDOM.createRoot(document.getElementById("app")).render(h(App));
