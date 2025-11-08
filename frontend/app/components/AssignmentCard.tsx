interface AssignmentCardProps {
  name: string;
  due_date: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';
  onPriorityChange?: (priority: 'low' | 'medium' | 'high') => void;
  onDescriptionChange?: (description: string) => void;
  showNotification?: boolean;
  onNotificationToggle?: () => void;
}

export default function AssignmentCard({ 
  name,
  due_date,
  description = '',
  priority,
  onPriorityChange,
  onDescriptionChange,
  showNotification = false,
  onNotificationToggle
}: AssignmentCardProps) {
  const priorityButtonStyles = (buttonPriority: 'low' | 'medium' | 'high') => {
    const isActive = priority === buttonPriority;
    const base = 'px-3 py-1.5 rounded border-2 text-sm font-bold transition-all min-w-[60px]';
    
    if (buttonPriority === 'low') {
      return `${base} ${isActive ? 'bg-green-500 text-white border-green-600' : 'bg-white text-black border-gray-300 hover:border-green-400'}`;
    } else if (buttonPriority === 'medium') {
      return `${base} ${isActive ? 'bg-yellow-500 text-white border-yellow-600' : 'bg-white text-black border-gray-300 hover:border-yellow-400'}`;
    } else {
      return `${base} ${isActive ? 'bg-red-500 text-white border-red-600' : 'bg-white text-black border-gray-300 hover:border-red-400'}`;
    }
  };

  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-200">
      {/* Assignment Title */}
      <div className="w-32 flex-shrink-0">
        <div className="font-medium text-sm text-black">{name}</div>
        <div className="text-xs text-gray-500">{due_date}</div>
      </div>

      {/* Priority Buttons */}
      <div className="flex gap-2 flex-shrink-0">
        <button
          onClick={() => onPriorityChange?.('low')}
          className={priorityButtonStyles('low')}
        >
          !
        </button>
        <button
          onClick={() => onPriorityChange?.('medium')}
          className={priorityButtonStyles('medium')}
        >
          !!
        </button>
        <button
          onClick={() => onPriorityChange?.('high')}
          className={priorityButtonStyles('high')}
        >
          !!!
        </button>
      </div>

      {/* Description Input */}
      <input
        type="text"
        value={description}
        onChange={(e) => onDescriptionChange?.(e.target.value)}
        placeholder="Brief Description"
        className="flex-1 px-3 py-1.5 border-2 border-gray-300 rounded text-sm text-black focus:outline-none focus:border-blue-400 placeholder:text-gray-400"
      />

      {/* Notification Bell */}
      <button
        onClick={onNotificationToggle}
        className={`flex-shrink-0 p-2 rounded border-2 transition-all ${
          showNotification 
            ? 'bg-yellow-400 border-yellow-500 text-white' 
            : 'bg-white border-gray-300 hover:border-yellow-400'
        }`}
        title="Toggle notification"
      >
        <span className="text-xl">🔔</span>
      </button>
    </div>
  );
}
