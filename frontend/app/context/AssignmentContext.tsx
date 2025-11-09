'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface Assignment {
  id: number;
  name: string;
  due_date: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  showNotification?: boolean;
}

interface AssignmentContextType {
  assignmentData: Assignment[];
  setAssignmentData: (data: Assignment[]) => void;
  handlePriorityChange: (index: number, priority: 'low' | 'medium' | 'high') => void;
  handleDescriptionChange: (index: number, description: string) => void;
  handleNotificationToggle: (index: number) => void;
  handleAddAssignment: () => void;
  studyPlan: string | null;
  setStudyPlan: (plan: string | null) => void;
}

const AssignmentContext = createContext<AssignmentContextType | undefined>(undefined);

export const AssignmentProvider = ({ children }: { children: ReactNode }) => {
  const [assignmentData, setAssignmentDataState] = useState<Assignment[]>([]);
  const [studyPlan, setStudyPlanState] = useState<string | null>(null);

  const setAssignmentData = (data: Assignment[]) => {
    setAssignmentDataState(data.map((assignment, index) => ({
      id: index + 1,
      name: assignment.name,
      due_date: assignment.due_date,
      description: "",
      priority: undefined,
      showNotification: false
    })));
  };

  const handlePriorityChange = (index: number, priority: 'low' | 'medium' | 'high') => {
    setAssignmentDataState((prev) =>
      prev.map((assignment, i) =>
        i === index ? { ...assignment, priority } : assignment
      )
    );
  };

  const handleDescriptionChange = (index: number, description: string) => {
    setAssignmentDataState((prev) =>
      prev.map((assignment, i) =>
        i === index ? { ...assignment, description } : assignment
      )
    );
  };

  const handleNotificationToggle = (index: number) => {
    setAssignmentDataState((prev) =>
      prev.map((assignment, i) =>
        i === index ? { ...assignment, showNotification: !assignment.showNotification } : assignment
      )
    );
  };

  const handleAddAssignment = () => {
    const newAssignment: Assignment = {
      id: assignmentData.length > 0 ? Math.max(...assignmentData.map(a => a.id)) + 1 : 1,
      name: `New Assignment ${assignmentData.length + 1}`,
      due_date: new Date().toISOString().split('T')[0],
      description: "",
      showNotification: false
    };
    setAssignmentDataState((prev) => [...prev, newAssignment]);
  };

  const setStudyPlan = (plan: string | null) => {
    setStudyPlanState(plan);
  };

  return (
    <AssignmentContext.Provider value={{ 
        assignmentData, 
        setAssignmentData,
        handlePriorityChange,
        handleDescriptionChange,
        handleNotificationToggle,
        handleAddAssignment,
        studyPlan,
        setStudyPlan
    }}>
      {children}
    </AssignmentContext.Provider>
  );
};

export const useAssignments = () => {
  const context = useContext(AssignmentContext);
  if (context === undefined) {
    throw new Error('useAssignments must be used within an AssignmentProvider');
  }
  return context;
};
