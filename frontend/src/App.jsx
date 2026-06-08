import { useState } from "react";
import "./index.css";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";

export default function App() {
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [refreshSessionsTrigger, setRefreshSessionsTrigger] = useState(0);

  const triggerSessionRefresh = () => {
    setRefreshSessionsTrigger(prev => prev + 1);
  };

  return (
    <div className="app-layout">
      <Sidebar 
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        refreshTrigger={refreshSessionsTrigger}
      />
      <ChatArea 
        activeSessionId={activeSessionId}
        onNewSessionCreated={(newId) => {
          setActiveSessionId(newId);
          triggerSessionRefresh();
        }}
        onNewChat={() => setActiveSessionId(null)}
      />
    </div>
  );
}
