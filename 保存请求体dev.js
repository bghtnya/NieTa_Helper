(async () => {
  const all = performance.getEntriesByType("resource");
  let text = "";
  for (let e of all) {
    text += `${e.name}\n`;
  }
  const blob = new Blob([text], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "urls.txt";
  a.click();
})();
