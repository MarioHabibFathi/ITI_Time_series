import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const app = createApp(App);
app.use(withStreamlitConnection);
//app.use(createPinia());
app.mount("#app");

Streamlit.setComponentReady();
Streamlit.setFrameHeight();
