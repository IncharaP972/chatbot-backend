import React, { useState } from 'react';

const NLP_API_URL = "http://localhost:5001/chat";

interface Message {
  from: "user" | "bot";
  text: string;
}

const ChatWidget: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      from: "bot",
      text: "Hello! I'm your AI assistant. Ask me anything and I'll reply in clear, concise language. 🔍"
    }
  ]);
  const [input, setInput] = useState<string>("");
  const [lang, setLang] = useState<string>("en");
  const [loading, setLoading] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { from: "user", text: userMessage }]);
    setLoading(true);
    setInput("");

    try {
      const response = await fetch(NLP_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, lang })
      });

      const data = await response.json();
      setMessages(prev => [
        ...prev,
        { from: "bot", text: data.response || "Sorry, I couldn't process that." }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { from: "bot", text: "Error connecting to the service. Please try again." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-5 right-5 bg-blue-600 hover:bg-blue-700 text-white rounded-full w-14 h-14 text-2xl shadow-lg z-50"
        title="Open AI Assistant"
      >
        {isOpen ? "✕" : "🤖"}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-20 right-5 w-96 max-w-[90vw] bg-white border border-gray-200 rounded-lg shadow-xl z-40">
          {/* Header */}
          <div className="bg-blue-600 text-white p-3 rounded-t-lg">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">AI Assistant</h3>
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value)}
                className="bg-blue-700 text-white text-sm rounded px-2 py-1"
              >
                <option value="en">English</option>
                <option value="hi">हिंदी</option>
                <option value="es">Español</option>
              </select>
            </div>
          </div>

          {/* Messages */}
          <div className="h-96 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${
                  msg.from === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    msg.from === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3 animate-pulse">
                  Thinking...
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t p-3">
            <div className="flex space-x-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask me anything..."
                className="flex-1 resize-none border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={1}
              />
              <button
                onClick={sendMessage}
                disabled={loading}
                className={`px-4 py-2 rounded-lg ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                } text-white`}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWidget;