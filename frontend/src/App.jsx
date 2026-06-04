// src/App.jsx
import "./index.css";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <ChatArea />
    </div>
  );
}
