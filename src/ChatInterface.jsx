import React, { useState, useEffect } from 'react';

const ChatInterface = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:7860/api/chat');
        setSocket(ws);

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            setMessages((prevMessages) => [...prevMessages, message]);
        };

        ws.onclose = () => console.log('WebSocket closed');
        ws.onerror = (error) => console.error('WebSocket error:', error);

        return () => ws.close();
    }, []);

    const sendMessage = () => {
        if (socket && input.trim()) {
            socket.send(input);
            setInput('');
        }
    };

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h2>Chat Interface</h2>
            <div style={{ border: '1px solid #ccc', padding: '10px', height: '300px', overflowY: 'scroll' }}>
                {messages.map((msg, index) => (
                    <div key={index} style={{ margin: '10px 0' }}>
                        <strong>{msg.type === 'user' ? 'User' : 'Agent'}:</strong> {msg.content}
                    </div>
                ))}
            </div>
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                style={{ width: '80%', padding: '10px' }}
            />
            <button onClick={sendMessage} style={{ padding: '10px', marginLeft: '10px' }}>
                Send
            </button>
        </div>
    );
};

export default ChatInterface;