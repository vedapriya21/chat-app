import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [clientId, setClientId] = useState(Math.floor(new Date().getTime() / 1000));
  const [websckt, setWbsckt] = useState(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const url = "ws://localhost:8000/ws/" + clientId;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "connect", clientId }));
    };

    ws.onmessage = (e) => {
      try {
        const receivedMessage = JSON.parse(e.data);
        setMessages((prevMessages) => [...prevMessages, receivedMessage]);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    setWbsckt(ws);

    return () => ws.close();
  }, [clientId]);

  const sendMessage = () => {
    if (!message.trim()) return;
    const msgData = { clientId, message };
    websckt.send(JSON.stringify(msgData));
    setMessage(""); 
  }; 
  return (
    <div className="container">
      <h1>Chat</h1>
      <h2>
        Your client ID: <strong>{clientId}</strong>
      </h2>
      <div className="chat-container">
        <div className="chat">
          {messages.map((msg, index) => (
            <div key={index} className={msg.clientId === clientId ? "my-message" : "other-message"}>
              <p className="client-id">Client ID: {msg.clientId}</p>
              <p>{msg.message}</p>
            </div>
          ))}
        </div>

        <div className="input-chat-container">
          <input
            className="input-chat"
            type="text"
            placeholder="Chat message ...."
            onChange={(e) => setMessage(e.target.value)}
            value={message}
          />
          <button className="submit-chat" onClick={sendMessage}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
