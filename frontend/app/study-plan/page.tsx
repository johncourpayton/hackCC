'use client'

import { useRouter } from 'next/navigation'
import { useAssignments } from '../context/AssignmentContext'

export default function StudyPlan() {
  const router = useRouter();
  const { assignmentData, studyPlan } = useAssignments();

  // Format the study plan text to preserve line breaks and formatting
  const formatStudyPlan = (text: string | null) => {
    if (!text) return null;
    
    // Split by double newlines to create paragraphs
    const paragraphs = text.split(/\n\n+/);
    
    return paragraphs.map((paragraph, index) => {
      // Check if paragraph starts with a number or bullet point
      const isList = /^[\d\-\*\•]/.test(paragraph.trim());
      const isHeading = /^#+\s/.test(paragraph.trim()) || /^[A-Z][^.!?]*:/.test(paragraph.trim());
      
      if (isHeading) {
        return (
          <h2 key={index} className="text-xl font-bold mt-6 mb-3 text-black">
            {paragraph.trim().replace(/^#+\s/, '')}
          </h2>
        );
      } else if (isList) {
        // Split list items
        const items = paragraph.split(/\n(?=[\d\-\*\•])/);
        return (
          <ul key={index} className="list-disc list-inside mb-4 space-y-2 text-black">
            {items.map((item, itemIndex) => (
              <li key={itemIndex} className="ml-4">
                {item.trim().replace(/^[\d\-\*\•]\s*/, '')}
              </li>
            ))}
          </ul>
        );
      } else {
        return (
          <p key={index} className="mb-4 text-black leading-relaxed whitespace-pre-line">
            {paragraph.trim()}
          </p>
        );
      }
    });
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

        {studyPlan ? (
          <div className="bg-white rounded-lg border-2 border-gray-800 p-8 shadow-lg">
            <div className="prose max-w-none">
              {formatStudyPlan(studyPlan)}
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
