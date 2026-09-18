function ClickConnect() {
  console.log("Checking connection status...");
  const colabButton = document.querySelector("colab-connect-button");
  if (colabButton && colabButton.shadowRoot) {
    const connectBtn = colabButton.shadowRoot.querySelector("#connect");
    if (connectBtn) {
      connectBtn.click();
      console.log("Connect button clicked ✅");
    } else {
      console.log("Connect button not found ❌");
    }
  } else {
    console.log("colab-connect-button element not found ❌");
  }
}
setInterval(ClickConnect, 60000); // Clicks every 60 seconds
