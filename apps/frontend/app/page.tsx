"use client";
import { useState, useRef, useEffect } from "react";
import { Bot, User, CornerDownLeft, Rabbit, GitPullRequest, TestTube2, Files, BrainCircuit, Loader2 } from "lucide-react";

// --- Mock Data ---
// In a real app, this would come from a real-time API connection (e.g., WebSockets)
const mockWorkflowSteps = [
    { id: 1, icon: BrainCircuit, title: "Planning", status: "completed", description: "Decomposing the task into smaller steps." },
    { id: 2, icon: Files, title: "Generating Code", status: "in_progress", description: "Writing files for the new API endpoint..." },
    { id: 3, icon: TestTube2, title: "Testing", status: "pending", description: "Running unit and integration tests." },
    { id: 4, icon: GitPullRequest, title: "Opening Pull Request", status: "pending", description: "Pushing code and creating a PR on GitHub." },
    { id: 5, icon: Rabbit, title: "CodeRabbitAI Review", status: "pending", description: "Awaiting automated code review." },
];

export default function MomentumApp() {
    const [prompt, setPrompt] = useState("");
    const [messages, setMessages] = useState([]);
    const [workflow, setWorkflow] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const lastMessageRef = useRef(null);

    useEffect(() => {
        lastMessageRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleInputChange = (e) => {
        setPrompt(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim() || isLoading) return;

        setError(null);
        setIsLoading(true);
        setWorkflow(mockWorkflowSteps.map(step => ({ ...step, status: step.id === 1 ? "in_progress" : "pending" }))); // Start workflow simulation

        const userMessage = { type: "user", text: prompt };
        setMessages(prev => [...prev, userMessage]);
        setPrompt("");

        try {
            const response = await fetch('http://127.0.0.1:8000/agent/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: prompt }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            const botMessage = { type: 'bot', text: result.message || "Agent run initiated. See progress on the right." };
            setMessages(prev => [...prev, botMessage]);

            // Simulate workflow progress for demonstration
            let currentStep = 1;
            const interval = setInterval(() => {
                setWorkflow(prev => prev.map(step => {
                    if (step.id === currentStep) return { ...step, status: 'completed' };
                    if (step.id === currentStep + 1) return { ...step, status: 'in_progress' };
                    return step;
                }));
                currentStep++;
                if (currentStep > mockWorkflowSteps.length) {
                    clearInterval(interval);
                    setIsLoading(false);
                }
            }, 2000);


        } catch (err) {
            console.error("Failed to start agent run:", err);
            const errorMessage = { type: 'bot', text: "Sorry, I couldn't connect to the agent. Please ensure the backend server is running." };
            setMessages(prev => [...prev, errorMessage]);
            setError("Failed to connect to the backend.");
            setWorkflow([]);
        } 
        // Note: setIsLoading(false) is handled by the simulation interval in the success case
    };

    const getStatusIndicator = (status) => {
        switch (status) {
            case 'completed':
                return <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center"><svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /></svg></div>;
            case 'in_progress':
                return <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse"></div>;
            case 'pending':
                return <div className="w-5 h-5 bg-gray-600 rounded-full"></div>;
            default:
                return null;
        }
    };

    return (
        <div className="flex h-screen bg-gray-900 text-gray-200 font-sans">
            {/* Left Panel: Chat Interface */}
            <div className="flex flex-col w-1/2 bg-gray-800 border-r border-gray-700">
                <header className="p-4 border-b border-gray-700">
                    <h1 className="text-xl font-bold">Momentum // Flow-State Agent</h1>
                </header>

                <div className="flex-1 p-6 overflow-y-auto">
                    <div className="space-y-6">
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex items-start gap-4 ${msg.type === 'user' ? 'justify-end' : ''}`}>
                                {msg.type === 'bot' && <Bot className="w-6 h-6 text-gray-400 flex-shrink-0" />}
                                <div className={`px-4 py-3 rounded-lg max-w-lg ${msg.type === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                                    <p className="text-sm">{msg.text}</p>
                                </div>
                                {msg.type === 'user' && <User className="w-6 h-6 text-gray-400 flex-shrink-0" />}
                            </div>
                        ))}
                         <div ref={lastMessageRef} />
                    </div>
                </div>

                <div className="p-4 border-t border-gray-700">
                    <form onSubmit={handleSubmit} className="flex items-center gap-3">
                        <input
                            type="text"
                            value={prompt}
                            onChange={handleInputChange}
                            placeholder="Describe the feature you want to build..."
                            className="flex-1 w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isLoading}
                        />
                        <button type="submit" className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center justify-center" disabled={isLoading}>
                           {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CornerDownLeft className="w-5 h-5" />}
                        </button>
                    </form>
                </div>
            </div>

            {/* Right Panel: Workflow Status */}
            <div className="flex flex-col w-1/2 p-6">
                <h2 className="text-lg font-semibold mb-6">Agent Workflow Status</h2>
                {error && <div className="bg-red-900/50 text-red-300 p-3 rounded-lg mb-4">{error}</div>}
                
                {workflow.length === 0 && !error && (
                     <div className="text-center text-gray-500 mt-10">
                        <BrainCircuit className="w-12 h-12 mx-auto mb-4" />
                        <p>The agent is idle.</p>
                        <p className="text-sm">Submit a prompt to begin a new task.</p>
                    </div>
                )}

                <div className="space-y-4">
                    {workflow.map((step, index) => (
                        <div key={step.id} className="flex items-start gap-4">
                            {getStatusIndicator(step.status)}
                            <div className="flex-1">
                                <h3 className="font-semibold">{step.title}</h3>
                                <p className="text-sm text-gray-400">{step.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

