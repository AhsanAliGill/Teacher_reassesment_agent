import React, { useState, useEffect } from 'react';

const evaluationSteps = [
  'Initializing AI Assessment Core...', 
  'Parsing Assessment Document...', 
  'Analyzing Teacher Performance Metrics...', 
  'Cross-referencing Pedagogical Standards...', 
  'Generating Actionable Feedback...', 
  'Compiling Final Evaluation Report...'
];

export const AiEvaluationLoader: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep(prevStep => (prevStep + 1) % evaluationSteps.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <style>
        {`
          @keyframes orbit {
            0% { transform: rotate(0deg) translateX(70px) rotate(0deg); }
            100% { transform: rotate(360deg) translateX(70px) rotate(-360deg); }
          }
          @keyframes orbit-reverse {
            0% { transform: rotate(0deg) translateX(90px) rotate(0deg); }
            100% { transform: rotate(-360deg) translateX(90px) rotate(360deg); }
          }
          @keyframes pulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 20px 5px rgba(79, 70, 229, 0.4); }
            50% { transform: scale(1.05); box-shadow: 0 0 30px 10px rgba(99, 102, 241, 0.6); }
          }
          .animate-orbit {
            animation: orbit 8s linear infinite;
          }
          .animate-orbit-reverse {
            animation: orbit-reverse 10s linear infinite;
          }
          .animate-inner-pulse {
            animation: pulse 3s ease-in-out infinite;
          }
        `}
      </style>
      <div className="flex flex-col items-center justify-center py-12 bg-gray-900/10 rounded-2xl shadow-2xl backdrop-blur-sm border border-white/10 w-full max-w-3xl my-8">
        <div className="relative flex items-center justify-center w-48 h-48 mb-6">
          {/* Outer Ring */}
          <div className="absolute w-48 h-48 border-2 border-indigo-400/50 rounded-full animate-spin" style={{ animationDuration: '15s' }}></div>
          {/* Middle Ring */}
          <div className="absolute w-36 h-36 border-2 border-cyan-400/60 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '12s' }}></div>
          {/* Inner Core */}
          <div className="absolute w-24 h-24 bg-indigo-600 rounded-full animate-inner-pulse"></div>
          
          {/* Orbiting Particles */}
          <div className="absolute w-3 h-3 bg-cyan-300 rounded-full animate-orbit"></div>
          <div className="absolute w-2 h-2 bg-violet-400 rounded-full animate-orbit-reverse"></div>
        </div>
        <div className="text-center">
          <h3 className="text-2xl font-semibold text-white mb-2">AI Evaluation in Progress</h3>
          <p className="text-lg text-indigo-300 font-medium transition-all duration-500 ease-in-out">
            {evaluationSteps[currentStep]}
          </p>
        </div>
      </div>
    </>
  );
};

export default AiEvaluationLoader;
