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
    handleAddAssignment,
    setStudyPlan
  } = useAssignments();
  const [showInstructions, setShowInstructions] = useState(false);
  const [showUserInfo, setShowUserInfo] = useState(false);
  const [canvasApiKey, setCanvasApiKey] = useState('');
  const [canvasUrl, setCanvasUrl] = useState('');
  const [discordIdNumber, setDiscordIdNumber] = useState('');
  const [isLoadingAssignments, setIsLoadingAssignments] = useState(false);
  const [isSavingUserInfo, setIsSavingUserInfo] = useState(false);

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

    // Collect assignments with notifications enabled
    const assignmentsWithNotifications = assignmentData
      .filter(assignment => assignment.showNotification)
      .map(assignment => ({
        name: assignment.name,
        description: assignment.description || '',
        priority: assignment.priority || 'none',
        due_date: assignment.due_date
      }));

    console.log('Study Plan Data:', JSON.stringify(assignmentJson, null, 2));

    try {
      // Send notifications for assignments with bell enabled (if any)
      if (assignmentsWithNotifications.length > 0) {
        try {
          const notificationResponse = await fetch('http://localhost:5000/api/notifications/assignments', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ assignments: assignmentsWithNotifications }),
          });

          if (notificationResponse.ok) {
            const notificationResult = await notificationResponse.json();
            console.log('Notifications sent:', notificationResult);
          } else {
            console.warn('Failed to send notifications, but continuing with study plan generation');
          }
        } catch (notificationError) {
          console.warn('Error sending notifications:', notificationError);
          // Continue with study plan generation even if notifications fail
        }
      }

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

      // Store the study plan in context (as JSON string for consistency)
      if (result.status === 'success' && result.study_plan) {
        // If it's already an object, stringify it; if it's a string, use it as-is
        const studyPlanToStore = typeof result.study_plan === 'string' 
          ? result.study_plan 
          : JSON.stringify(result.study_plan);
        setStudyPlan(studyPlanToStore);
      } else {
        throw new Error(result.message || 'Failed to generate study plan');
      }

      // Navigate to study plan page
      router.push('/study-plan');
    } catch (error) {
      console.error('Error generating study plan:', error);
      alert('Failed to generate study plan. Please try again.');
    }
  }

  const handlePullInfo = async () => {
    setIsLoadingAssignments(true);
    try {
      const response = await fetch('/api/canvas'); // Call the new Next.js API route
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: Assignment[] = await response.json();
      setAssignmentData(data);
    } catch (error) {
      console.error("Failed to fetch assignments:", error);
      // Optionally show an error message to the user
      alert('Failed to fetch assignments. Please check your Canvas API key and domain in "My Info".');
    } finally {
      setIsLoadingAssignments(false);
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

    setIsSavingUserInfo(true);

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
      alert('Failed to save settings. Please try again.');
    } finally {
      setIsSavingUserInfo(false);
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
          disabled={isLoadingAssignments}
          className={`px-8 py-3 rounded border-2 border-gray-800 font-medium text-lg text-black ${
            isLoadingAssignments 
              ? 'bg-gray-300 cursor-not-allowed opacity-50' 
              : 'hover:bg-gray-100'
          }`}
        >
          {isLoadingAssignments ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            'Pull Info'
          )}
        </button>
      </div>
      
      {/* Assignment List */}
      <div className="max-w-6xl mx-auto bg-white rounded-lg border-2 border-gray-800 p-6 mb-6">
        {isLoadingAssignments ? (
          <div className="text-center text-black py-8">
            <div className="flex flex-col items-center justify-center gap-4">
              <svg className="animate-spin h-8 w-8 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-lg font-medium">Loading assignments from Canvas...</p>
              <p className="text-sm text-gray-600">This may take a few moments</p>
            </div>
          </div>
        ) : assignmentData.length === 0 ? (
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
                disabled={isSavingUserInfo || !canvasApiKey.trim() || !canvasUrl.trim()}
                className={`w-full px-4 py-2 rounded border-2 border-gray-800 font-medium text-black ${
                  isSavingUserInfo || !canvasApiKey.trim() || !canvasUrl.trim()
                    ? 'bg-gray-300 cursor-not-allowed opacity-50' 
                    : 'hover:bg-gray-100'
                }`}
              >
                {isSavingUserInfo ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </span>
                ) : (
                  'Save'
                )}
              </button>
            </div>
          </div>
        </div>          
      )}
    </div>
  );
}

