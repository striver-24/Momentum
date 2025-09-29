import React, { useState, useRef, useEffect } from 'react';
import { Play, Loader, CheckCircle, XCircle, Bot, Code, GitPullRequest, Search } from 'lucide-react';

// Main App Component
const App = () => {
    const [prompt, setPrompt] = useState('');
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('idle'); // idle, working, success, error
    const [pullRequestUrl, setPullRequestUrl] = useState('');
    const logsEndRef = useRef(null);

    const scrollToBottom = () => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [logs]);

    const mockWorkflow = async () => {
        const addLog = (icon, message, delay) => {
            return new Promise(resolve => {
                setTimeout(() => {
                    setLogs(prev => [...prev, { icon, message, time: new Date().toLocaleTimeString() }]);
                    resolve();
                }, delay);
            });
        };

        setLogs([]);
        setPullRequestUrl('');
        setStatus('working');

        await addLog(<Bot className="w-5 h-5 text-indigo-400" />, "Agent initiated. Analyzing requirements...", 500);
        await addLog(<Search className="w-5 h-5 text-sky-400" />, "Scanning codebase for context...", 1000);
        await addLog(<Bot className="w-5 h-5 text-indigo-400" />, "Generating high-level plan: [1. Create API route, 2. Add business logic, 3. Write unit tests]", 1500);
        await addLog(<Code className="w-5 h-5 text-emerald-400" />, "Generating code for API route `/api/tasks`...", 2000);
        await addLog(<Play className="w-5 h-5 text-amber-400" />, "Running unit tests... 2 passed, 0 failed.", 2500);
        await addLog(<GitPullRequest className="w-5 h-5 text-gray-400" />, "Committing changes and creating pull request...", 1500);
        
        const fakePrUrl = "https://github.com/your-org/your-repo/pull/123";
        setPullRequestUrl(fakePrUrl);
        await addLog(<Bot className="w-5 h-5 text-indigo-400" />, `Pull request created successfully. Waiting for CodeRabbitAI review...`, 1000);

        // Simulate CodeRabbitAI review
        await addLog(<img src="https://coderabbit.ai/logo.svg" alt="CodeRabbit AI" className="w-5 h-5" />, "CodeRabbitAI review in progress...", 3000);
        await addLog(<img src="https://coderabbit.ai/logo.svg" alt="CodeRabbit AI" className="w-5 h-5" />, "Review complete. 1 suggestion found.", 2000);
        await addLog(<Bot className="w-5 h-5 text-indigo-400" />, "Applying feedback from CodeRabbitAI...", 1000);
        await addLog(<Code className="w-5 h-5 text-emerald-400" />, "Refactoring code based on suggestions...", 2000);
        await addLog(<Play className="w-5 h-5 text-amber-400" />, "Re-running tests... all tests passed.", 1500);
        await addLog(<CheckCircle className="w-5 h-5 text-green-500" />, "All checks passed. Ready for merge.", 1000);
        setStatus('success');
    };


    const handleSubmit = (e) => {
        e.preventDefault();
        if (!prompt.trim() || status === 'working') return;
        mockWorkflow();
    };

    const getStatusIndicator = () => {
        switch (status) {
            case 'working':
                return <div className="flex items-center gap-2"><Loader className="w-4 h-4 animate-spin" /><span>Working...</span></div>;
            case 'success':
                return <div className="flex items-center gap-2 text-green-400"><CheckCircle className="w-4 h-4" /><span>Completed</span></div>;
            case 'error':
                return <div className="flex items-center gap-2 text-red-400"><XCircle className="w-4 h-4" /><span>Error</span></div>;
            default:
                return <div className="flex items-center gap-2 text-gray-400"><span>Idle</span></div>;
        }
    };

    return (
        <div className="bg-gray-900 text-gray-200 font-sans min-h-screen flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-4xl bg-gray-800 border border-gray-700 rounded-2xl shadow-2xl shadow-indigo-900/20 flex flex-col" style={{ minHeight: '80vh' }}>
                {/* Header */}
                <header className="flex items-center justify-between p-4 border-b border-gray-700">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">Momentum</h1>
                            <p className="text-sm text-gray-400">The "Flow-State" Engineering Agent</p>
                        </div>
                    </div>
                    <div className="text-sm px-3 py-1.5 bg-gray-700/50 border border-gray-600 rounded-full">
                        {getStatusIndicator()}
                    </div>
                </header>

                {/* Main Content */}
                <main className="flex-grow p-6 flex flex-col gap-6 overflow-hidden">
                    {/* Input Section */}
                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        <label htmlFor="prompt" className="text-md font-medium text-gray-300">Enter Business Requirement</label>
                        <textarea
                            id="prompt"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            placeholder="e.g., 'Create a new API endpoint /users/{id} that retrieves user data from the database...'"
                            className="w-full h-24 p-3 bg-gray-900 border border-gray-700 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-shadow"
                            disabled={status === 'working'}
                        />
                        <button
                            type="submit"
                            disabled={status === 'working' || !prompt.trim()}
                            className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-lg shadow-md hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {status === 'working' ? <Loader className="animate-spin" /> : <Play />}
                            <span>{status === 'working' ? 'Generating...' : 'Generate Code'}</span>
                        </button>
                    </form>

                    {/* Output Section */}
                    <div className="flex-grow flex flex-col bg-gray-900/70 border border-gray-700 rounded-lg p-4 overflow-hidden">
                       <h2 className="text-md font-medium text-gray-300 mb-3 flex-shrink-0">Agent Activity</h2>
                       <div className="flex-grow overflow-y-auto pr-2">
                           {logs.map((log, index) => (
                               <div key={index} className="flex items-start gap-3 text-sm mb-2 font-mono">
                                   <div className="mt-1">{log.icon}</div>
                                   <span className="text-gray-500">{log.time}</span>
                                   <p className="flex-1 text-gray-300">{log.message}</p>
                               </div>
                           ))}
                           <div ref={logsEndRef} />
                       </div>
                       {status === 'success' && pullRequestUrl && (
                           <div className="mt-4 p-4 bg-green-900/30 border border-green-700 rounded-lg flex items-center justify-between">
                               <div>
                                   <p className="font-semibold text-green-300">Pull Request Ready</p>
                                   <a href={pullRequestUrl} target="_blank" rel="noopener noreferrer" className="text-sm text-indigo-400 hover:underline">{pullRequestUrl}</a>
                               </div>
                               <a href={pullRequestUrl} target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-semibold transition-colors">
                                   View PR
                               </a>
                           </div>
                       )}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default App;
