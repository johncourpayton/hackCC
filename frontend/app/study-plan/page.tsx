'use client'

import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'

interface Assignment {
  id: string;
  title: string;
  dueDate: string;
  course: string;
  // Add more properties as needed
}

export default function StudyPlan() {
  const router = useRouter();
  const [assignments, setAssignments] = useState<Assignment[]>([]);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={() => router.back()}
          className="px-4 py-2 rounded-lg hover:bg-gray-100 border border-gray-200"
        >
          ← Back
        </button>
        <h1 className="text-2xl font-bold">Study Plan</h1>
      </div>

      <div className="grid gap-4">
        {assignments.map((assignment) => (
          <div 
            key={assignment.id}
            className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <h3 className="font-bold text-lg">{assignment.title}</h3>
            <div className="text-gray-600">
              <p>Course: {assignment.course}</p>
              <p>Due: {assignment.dueDate}</p>
            </div>
          </div>
        ))}

        {assignments.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No assignments found. Please pull assignment data from the home page.
          </div>
        )}
      </div>
    </div>
  );
}