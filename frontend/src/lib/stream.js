export const streamChat = async (response, onToken, onDone) => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.replace("data:", "").trim();
      if (!payload) continue;
      const event = JSON.parse(payload);
      if (event.type === "token") {
        onToken(event.value);
      }
      if (event.type === "done") {
        onDone(event);
      }
    }
  }
};
