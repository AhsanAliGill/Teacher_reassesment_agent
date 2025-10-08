import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, XCircle, BrainCircuit, FileUp, PartyPopper, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface Question {
  id: string;
  question_text: string;
  marks: number;
}

interface AssessmentData {
  id: string;
  subject_name: string;
  file_name: string;
  questions: Question[];
}

export const AssessmentUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setAssessmentData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/api/assessments/process-file', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok && result.status === 'success') {
        setAssessmentData(result.data);
      } else {
        setError(result.message || 'Failed to process the file.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full flex flex-col items-center px-4 py-8">
      <Card className="w-full max-w-4xl shadow-xl mb-8 glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-2xl text-foreground">
            <FileUp className="w-8 h-8 text-blue-500" />
            Upload Original Assessment Paper
          </CardTitle>
          <CardDescription>Upload the paper, and the AI will extract the questions for you.</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`relative rounded-xl p-8 text-center transition-all duration-300 ease-in-out cursor-pointer group ${
              isDragging
                ? 'border-4 border-dashed border-blue-400 bg-blue-100 scale-105 shadow-lg'
                : 'border-2 border-dashed border-gray-300 bg-gray-50'
            } ${
              selectedFile
                ? 'border-solid border-green-500 bg-green-50'
                : 'hover:border-blue-400 hover:bg-blue-50 hover:shadow-md'
            }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => !selectedFile && inputRef.current?.click()}
          >
            {selectedFile ? (
              <div className="flex flex-col items-center justify-center gap-4 text-green-700">
                <CheckCircle2 className="w-16 h-16 text-green-500" />
                <div className="text-center">
                  <p className="font-semibold text-lg">File Ready!</p>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="absolute top-2 right-2 text-gray-500 hover:text-red-600 transition-colors"
                  aria-label="Remove file"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-4 text-gray-600">
                <Upload
                  className={`w-16 h-16 text-gray-400 transition-transform duration-300 ease-in-out ${
                    isDragging ? 'scale-110 text-blue-600' : 'group-hover:scale-110 group-hover:text-blue-500'
                  }`}
                />
                <div className="text-center">
                  <p className="font-semibold text-lg">Drop your assessment file here</p>
                  <p className="text-gray-500">or click to browse</p>
                </div>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {error && <div className="mt-4 text-center text-sm text-red-600 bg-red-100 p-3 rounded-md">{error}</div>}

                    <Button 
            onClick={handleUpload} 
            className="w-full mt-6 text-white font-bold text-lg py-3 rounded-lg shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 ease-in-out bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-lg"
            disabled={!selectedFile || isLoading}
          >
            {isLoading ? (
                <span className="flex items-center justify-center">
                    <BrainCircuit className="w-6 h-6 mr-2 animate-spin" />
                    Processing...
                </span>
            ) : (
                <span className="flex items-center justify-center">
                    <Sparkles className="w-6 h-6 mr-2" />
                    Extract Questions
                </span>
            )}
          </Button>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="w-full max-w-4xl">
            <div className="flex flex-col items-center justify-center py-12 bg-gray-900/10 rounded-2xl shadow-2xl backdrop-blur-sm border border-white/10 w-full my-8">
                <div className="relative flex items-center justify-center w-48 h-48 mb-6">
                    <div className="absolute w-48 h-48 border-2 border-blue-400/50 rounded-full animate-spin" style={{ animationDuration: '15s' }}></div>
                    <div className="absolute w-36 h-36 border-2 border-cyan-400/60 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '12s' }}></div>
                    <div className="absolute w-24 h-24 bg-blue-600 rounded-full animate-pulse"></div>
                    <BrainCircuit className="absolute w-16 h-16 text-cyan-200 animate-pulse" style={{animationDuration: '2s'}}/>
                </div>
                <div className="text-center">
                    <h3 className="text-2xl font-semibold text-white mb-2">AI is Processing Paper</h3>
                    <p className="text-lg text-blue-300 font-medium">Extracting questions, please wait...</p>
                </div>
            </div>
        </div>
      )}

      {assessmentData && (
        <Card className="w-full max-w-4xl shadow-xl mt-8 glass-card slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-2xl text-foreground">
                <FileText className="w-8 h-8 text-green-500" />
                Extracted Questions
            </CardTitle>
            <CardDescription>Subject: {assessmentData.subject_name}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="p-6 bg-green-100/50 border-2 border-dashed border-green-500 rounded-2xl text-center">
                  <PartyPopper className="w-16 h-16 text-green-600 mx-auto mb-4 animate-bounce" />
                  <h3 className="text-2xl font-bold text-green-800 mb-2">Assessment Processed!</h3>
                  <p className="text-lg text-green-700">
                      Your assessment, <strong>{assessmentData.subject_name}</strong>, has been successfully saved. You can now evaluate student papers for this subject.
                  </p>
              </div>
              {assessmentData.questions.map((q, index) => (
                <div key={q.id} className="p-6 bg-white/10 rounded-xl border border-white/20 shadow-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-lg font-semibold text-foreground">Question {index + 1}</h4>
                    <span className="px-3 py-1 text-sm font-bold text-blue-800 bg-blue-200 rounded-full">{q.marks} Marks</span>
                  </div>
                  <p className="text-foreground/90 whitespace-pre-wrap">{q.question_text}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AssessmentUpload;
