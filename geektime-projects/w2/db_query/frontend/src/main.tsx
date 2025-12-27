import React from "react";
import ReactDOM from "react-dom/client";
import { Refine } from "@refinedev/core";
import { BrowserRouter } from "react-router-dom";
import dataProvider from "@refinedev/simple-rest";
import App from "./App";

// Create data provider using our API client
const apiUrl = "/api/v1";

const customDataProvider = dataProvider(apiUrl);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Refine
        dataProvider={customDataProvider}
        resources={[
          {
            name: "dbs",
          },
        ]}
      >
        <App />
      </Refine>
    </BrowserRouter>
  </React.StrictMode>
);
