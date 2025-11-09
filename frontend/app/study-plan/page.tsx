'use client'

import { useRouter } from 'next/navigation'
import { useAssignments } from '../context/AssignmentContext'

interface ScheduleDay {
  day: string;
  date: string;
  assignments: Array<{
    name: string;
    time: string;
    duration: string;
    priority: string;
  }>;
}

interface StudyPlanData {
  schedule: ScheduleDay[];
  error?: string;
  raw_response?: string;
}

export default function StudyPlan() {
  const router = useRouter();
  const { assignmentData, studyPlan } = useAssignments();

  // Parse study plan - could be JSON object or string
  const parseStudyPlan = (plan: string | null): StudyPlanData | null => {
    if (!plan) return null;
    
    try {
      // Try parsing as JSON first
      const parsed = typeof plan === 'string' ? JSON.parse(plan) : plan;
      if (parsed && parsed.schedule && Array.isArray(parsed.schedule)) {
        return parsed;
      }
    } catch (e) {
      // If parsing fails, return null (fallback to old format)
      console.warn('Failed to parse study plan as JSON:', e);
    }
    
    return null;
  };

  const studyPlanData = parseStudyPlan(studyPlan);

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'low':
        return 'bg-green-100 border-green-300 text-green-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => router.back()}
            className="px-4 py-2 rounded-lg hover:bg-gray-100 border border-gray-200 text-black"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-black">Study Plan</h1>
          <div className="w-20"></div> {/* Spacer for centering */}
        </div>

        {studyPlanData && studyPlanData.schedule && studyPlanData.schedule.length > 0 ? (
          <div className="bg-white rounded-lg border-2 border-gray-800 p-8 shadow-lg">
            <h2 className="text-2xl font-bold mb-6 text-black">Study Schedule</h2>
            <div className="space-y-6">
              {studyPlanData.schedule.map((day, dayIndex) => (
                <div key={dayIndex} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
                  <h3 className="text-xl font-semibold mb-4 text-black">{day.day}</h3>
                  {day.assignments && day.assignments.length > 0 ? (
                    <div className="space-y-3">
                      {day.assignments.map((assignment, assignmentIndex) => (
                        <div
                          key={assignmentIndex}
                          className="p-4 rounded-lg border-2 border-gray-200 hover:shadow-md transition-shadow bg-gray-50"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-bold text-lg text-black flex-1">{assignment.name}</h4>
                            {assignment.priority && (
                              <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getPriorityColor(assignment.priority)}`}>
                                {assignment.priority.toUpperCase()}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-gray-600">
                            <span className="flex items-center">
                              <span className="mr-2">🕐</span>
                              {assignment.time}
                            </span>
                            {assignment.duration && (
                              <span className="flex items-center">
                                <span className="mr-2">⏱️</span>
                                {assignment.duration}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg border-2 border-gray-200 bg-gray-50">
                      <p className="text-gray-500 italic text-center">No assignments scheduled for this day</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : studyPlan ? (
          <div className="bg-white rounded-lg border-2 border-gray-800 p-8 shadow-lg">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-black">{studyPlan}</pre>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg border-2 border-gray-800 p-8">
            <div className="text-center text-gray-500 py-8">
              <p className="mb-4">No study plan generated yet.</p>
              <p>Please go back and click "Generate Study Plan" to create a personalized study plan based on your assignments.</p>
            </div>
          </div>
        )}

        {/* Show assignments list below study plan */}
        {assignmentData.length > 0 && (
          <div className="mt-8 bg-white rounded-lg border-2 border-gray-800 p-6">
            <h2 className="text-xl font-bold mb-4 text-black">Your Assignments</h2>
            <div className="grid gap-4">
              {assignmentData.map((assignment) => (
                <div 
                  key={assignment.id}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <h3 className="font-bold text-lg text-black">{assignment.name}</h3>
                  <div className="text-gray-600">
                    <p>Due: {assignment.due_date}</p>
                    {assignment.priority && (
                      <p className="mt-1">
                        Priority: <span className="font-semibold capitalize">{assignment.priority}</span>
                      </p>
                    )}
                    {assignment.description && (
                      <p className="mt-1 text-sm">{assignment.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
