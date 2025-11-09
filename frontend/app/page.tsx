'use client'

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation"
import AssignmentCard from "./components/AssignmentCard";
import { useAssignments } from "./context/AssignmentContext";

interface Assignment {
  id: number;
  name: string; // Changed from title to name
  due_date: string; // Changed from dueDate to due_date
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  showNotification?: boolean;
}

export default function Home() {
  const router = useRouter();
  const { 
    assignmentData, 
    setAssignmentData, 
    handlePriorityChange, 
    handleDescriptionChange, 
    handleNotificationToggle, 
    handleAddAssignment 
  } = useAssignments();
  const [showInstructions, setShowInstructions] = useState(false);
  const [showUserInfo, setShowUserInfo] = useState(false);
  const [canvasApiKey, setCanvasApiKey] = useState('');
  const [canvasUrl, setCanvasUrl] = useState('');
  const [discordIdNumber, setDiscordIdNumber] = useState('');

  const handleHowToButton = () => {
    setShowInstructions(!showInstructions);
  }

  const handleLoadStudyPlanPage = async () => {
    // Collect assignment data
    const assignmentJson = assignmentData.map(assignment => ({
      name: assignment.name,
      description: assignment.description || '',
      priority: assignment.priority || 'none',
      due_date: assignment.due_date
    }));

    console.log('Study Plan Data:', JSON.stringify(assignmentJson, null, 2));

    try {
      // Send data to Python backend for Gemini processing
      const response = await fetch('http://localhost:5000/generate-study-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ assignments: assignmentJson }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate study plan');
      }

      const result = await response.json();
      console.log('Gemini Response:', result);

      // Navigate to study plan page
      router.push('/study-plan');
    } catch (error) {
      console.error('Error generating study plan:', error);
      alert('Failed to generate study plan. Please try again.');
    }
  }

  const handlePullInfo = async () => {
    try {
      const response = await fetch('/api/canvas'); // Call the new Next.js API route
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: Assignment[] = await response.json();
      setAssignmentData(data);
    } catch (error) {
      console.error("Failed to fetch assignments:", error);
    }
  };

  const handleUserInfoPopup = () => {
    setShowUserInfo(!showUserInfo);
  } 

  const saveUserInformation = async () => {
    let trimmedUrl = canvasUrl.trim();
    trimmedUrl = trimmedUrl.replace(/^https?:\/\//, "");
    const match = trimmedUrl.match(/^([^\/]+\.com)/);
    trimmedUrl = match ? match[1] : trimmedUrl;

    if (!canvasApiKey.trim() || !trimmedUrl) return;

    console.log("url: " + trimmedUrl)
    console.log("apiKey: " + canvasApiKey)
    console.log("discord_id: " + discordIdNumber)

    try {
      const response = await fetch('http://localhost:5000/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apiKey: canvasApiKey.trim(),
          canvasDomain: trimmedUrl,
          discordId: discordIdNumber
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      // Close the modal after successful save
      handleUserInfoPopup();
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };
    
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 max-w-6xl mx-auto">
        <button 
          onClick={handleHowToButton} 
          className="px-6 py-2 rounded border-2 border-gray-800 hover:bg-gray-100 font-medium text-black"
        >
          How To Use
        </button>
        <div className="text-2xl font-bold text-black">Canvas Companion</div>
        <button 
          onClick = {handleUserInfoPopup}
          className="px-6 py-2 rounded border-2 border-gray-800 hover:bg-gray-100 font-medium text-black"
        >
          My Info
        </button>
      </div>

      {/* Pull Info Button */}
      <div className="flex justify-center mb-8">
        <button 
          onClick={handlePullInfo}
          className="px-8 py-3 rounded border-2 border-gray-800 hover:bg-gray-100 font-medium text-lg text-black"
        >
          Pull Info
        </button>
      </div>
      
      {/* Assignment List */}
      <div className="max-w-6xl mx-auto bg-white rounded-lg border-2 border-gray-800 p-6 mb-6">
        {assignmentData.length === 0 ? (
          <div className="text-center text-black py-8">
            No assignments loaded. Click "Pull Info" to fetch assignments.
          </div>
        ) : (
          assignmentData.map((assignment, i) => (
            <AssignmentCard
              key={assignment.id}
              name={assignment.name}
              due_date={assignment.due_date}
              description={assignment.description}
              priority={assignment.priority}
              showNotification={assignment.showNotification}
              onPriorityChange={(priority: 'low' | 'medium' | 'high') => handlePriorityChange(i, priority)}
              onDescriptionChange={(description: string) => handleDescriptionChange(i, description)}
              onNotificationToggle={() => handleNotificationToggle(i)}
            />
          ))
        )}
        
        {/* Add Button */}
        {assignmentData.length > 0 && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleAddAssignment}
              className="px-8 py-2 rounded border-2 border-gray-800 hover:bg-gray-100 font-bold text-xl text-black"
            >
              +
            </button>
          </div>
        )}
      </div>

      {/* Generate Study Plan Button */}
      <div className="flex justify-center">
        <button  
          onClick={handleLoadStudyPlanPage} 
          className="px-8 py-3 rounded border-2 border-gray-800 hover:bg-gray-100 font-medium text-lg text-black"
        >
          Generate Study Plan
        </button>
      </div>

      {/* Instructions Modal */}
      {showInstructions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full m-4 border-2 border-gray-800">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-black">How to Use</h2>
              <button 
                onClick={handleHowToButton}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            <div className="text-black">
              <p className="mb-2">1. Click "Pull Info" to load your assignments from Canvas</p>
              <p className="mb-2">2. Set priority levels (!/!!/!!!) for each assignment</p>
              <p className="mb-2">3. Add brief descriptions to help remember important details</p>
              <p className="mb-2">4. Toggle bell icon to enable notifications for assignments</p>
              <p className="mb-2">5. Click "+" to add custom assignments</p>
              <p>6. Click "Generate Study Plan" to create a personalized study schedule</p>
            </div>
          </div>
        </div>
      )}

      {showUserInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full m-4 border-2 border-gray-800">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-black">Input User Information</h2>
              <button 
                onClick={handleUserInfoPopup}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            <div className="text-black">

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Discord Id Number
                </label>
                <input
                  type="text"
                  value={discordIdNumber}
                  onChange={(e) => setDiscordIdNumber(e.target.value)}
                  placeholder="Enter your Discord ID #"
                  required
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded text-black focus:outline-none focus:border-blue-400"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Canvas API Key
                </label>
                <input
                  type="text"
                  value={canvasApiKey}
                  onChange={(e) => setCanvasApiKey(e.target.value)}
                  placeholder="Enter your Canvas API key"
                  required
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded text-black focus:outline-none focus:border-blue-400"
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  School Canvas URL
                </label>
                <input
                  type="url"
                  value={canvasUrl}
                  onChange={(e) => setCanvasUrl(e.target.value)}
                  placeholder="e.g., https://yourschool.instructure.com"
                  required
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded text-black focus:outline-none focus:border-blue-400"
                />
              </div>

              <button
                onClick={saveUserInformation}
                className="w-full px-4 py-2 rounded border-2 border-gray-800 hover:bg-gray-100 font-medium text-black"
                disabled ={!canvasApiKey.trim() || !canvasUrl.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>          
      )}
    </div>
  );
}
