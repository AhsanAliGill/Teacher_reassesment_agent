import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { AiEvaluationLoader } from './AiEvaluationLoader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface UploadResponse {
  status: string;
  message: string;
  data?: {
    file_paths: string[];
  };
}

export const ReassessmentPdfUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [reports, setReports] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const loaderRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setSelectedFile(null);
      setError('Please select a PDF file.');
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
    } else {
      setSelectedFile(null);
      setError('Please select a PDF file.');
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

  useEffect(() => {
    if (isGenerating) {
      loaderRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isGenerating]);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('No file selected.');
      return;
    }
    setIsUploading(true);
    setError(null);
    setUploadResponse(null);

    const formData = new FormData();
    formData.append('files', selectedFile);

    try {
      const res = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/api/reports/upload-files', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadResponse(data);
        if (data.data?.file_paths && data.data.file_paths.length > 0) {
          setIsGenerating(true);
          try {
            const genRes = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/api/reports/generate', {
              method: 'POST',
              headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ file_paths: [data.data.file_paths[0]] }),
            });
            const genData = await genRes.json();
            if (genRes.ok && typeof genData.data === 'string' && genData.data.trim().length > 0) {
              console.log('Raw report data:', genData.data); // Debug raw report
              setReports(prevReports => [...prevReports, genData.data]);
            } else {
              setError('No report content was returned by the server.');
            }
          } catch {
            setError('An error occurred while generating the report.');
          } finally {
            setIsGenerating(false);
          }
        } else {
          setError('No file paths returned from the server.');
        }
      } else {
        setError(data.message || 'Upload failed.');
      }
    } catch {
      setError('An error occurred while uploading.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full min-h-screen bg-gray-100 flex flex-col items-center px-4 py-8">
      {/* Upload Form Card */}
      <Card className="w-full max-w-3xl shadow-xl mb-8 bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl text-indigo-800">
            <Upload className="w-6 h-6 text-indigo-600" />
            Upload Reassessment PDF
          </CardTitle>
          <CardDescription>Upload your reassessment answer sheet (PDF only, max 20MB).</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`relative rounded-xl p-8 text-center transition-all duration-300 ease-in-out cursor-pointer group ${
              isDragging
                ? 'border-4 border-dashed border-indigo-400 bg-indigo-100 scale-105 shadow-lg'
                : 'border-2 border-dashed border-gray-300 bg-gray-50'
            } ${
              selectedFile
                ? 'border-solid border-green-500 bg-green-50'
                : 'hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-md'
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
                    isDragging ? 'scale-110 text-indigo-600' : 'group-hover:scale-110 group-hover:text-indigo-500'
                  }`}
                />
                <div className="text-center">
                  <p className="font-semibold text-lg">Drop your PDF here</p>
                  <p className="text-gray-500">or click to browse</p>
                  <p className="text-xs text-gray-400 mt-2">Maximum file size: 20MB</p>
                </div>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}

          <Button onClick={handleUpload} className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700" disabled={!selectedFile || isUploading}>
            {isUploading ? 'Uploading...' : 'Upload PDF'}
          </Button>
        </CardContent>
      </Card>

      {/* Upload Response Card */}
      {uploadResponse && (
        <Card className="w-full max-w-3xl shadow-lg mb-8 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-green-800 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Upload Response
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded bg-green-50 border border-green-200 text-green-800 text-sm overflow-auto break-words" style={{ wordBreak: 'break-word', maxHeight: 400 }}>
              <div className="font-semibold">{uploadResponse.message}</div>
              {uploadResponse.data?.file_paths && (
                <div className="mt-2">
                  <span>File Path: </span>
                  <code className="break-all bg-green-100 px-1 py-0.5 rounded text-xs">{uploadResponse.data.file_paths[0]}</code>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div ref={loaderRef} className="w-full flex flex-col items-center"> 
        {isGenerating && <AiEvaluationLoader />}

        {reports.length > 0 && reports.map((report, index) => (
        <Card key={index} className="w-full max-w-3xl shadow-xl border-indigo-100 bg-white">
          <CardHeader>
            <CardTitle className="text-2xl text-indigo-800 flex items-center gap-2">
              <FileText className="w-6 h-6 text-indigo-600" />
              Reassessment Report
            </CardTitle>
            {/* Debug: Show raw report */}
            <details className="mt-2 text-sm text-gray-600">
              <summary className="cursor-pointer">View Raw Report</summary>
              <pre className="bg-gray-50 p-3 rounded mt-2 text-xs overflow-auto max-h-60">{report}</pre>
            </details>
          </CardHeader>
          <CardContent className="flex flex-col gap-8">
            {(() => {
              // --- Report Parsing Helper Functions ---
              const parseReport = (reportStr: string) => {
                const sections: any[] = [];
                const normalizedReport = reportStr.replace(/\r\n/g, '\n').trim();

                // Split the report into lines
                const lines = normalizedReport.split('\n');

                let studentDetails: Record<string, string> | null = null;
                let questions: Record<string, string>[] = [];
                let currentQuestion: Record<string, string> | null = null;
                let isStudentSection = false;
                let isQuestionSection = false;

                lines.forEach(line => {
                  const trimmedLine = line.trim();
                  if (trimmedLine.startsWith('- **Student Details**:')) {
                    isStudentSection = true;
                    isQuestionSection = false;
                    studentDetails = {};
                    return;
                  }

                  if (trimmedLine.startsWith('- **Question-by-Question Evaluation**:')) {
                    isStudentSection = false;
                    isQuestionSection = true;
                    if (currentQuestion) {
                      questions.push(currentQuestion);
                      currentQuestion = null;
                    }
                    return;
                  }

                  const fieldMatch = trimmedLine.match(/^-\s*\*\*(.*?)\*\*:\s*(.*)/);
                  if (fieldMatch) {
                    const key = fieldMatch[1].trim();
                    const value = fieldMatch[2].trim();

                    if (isStudentSection && studentDetails) {
                      studentDetails[key] = value;
                    } else if (isQuestionSection) {
                      if (key === 'Question Number') {
                        if (currentQuestion) {
                          questions.push(currentQuestion);
                        }
                        currentQuestion = { [key]: value };
                      } else if (currentQuestion) {
                        currentQuestion[key] = value;
                      }
                    }
                  } else if (currentQuestion) {
                    // Append to the last key if it's a multi-line value
                    const lastKey = Object.keys(currentQuestion).pop();
                    if (lastKey) {
                      currentQuestion[lastKey] += '\n' + line.trim();
                    }
                  }
                });

                if (currentQuestion) {
                  questions.push(currentQuestion);
                }

                if (studentDetails) {
                  sections.push({ type: 'student', content: studentDetails });
                }

                if (questions.length > 0) {
                  sections.push({ type: 'header', content: 'Question-by-Question Evaluation' });
                  questions.forEach((q, idx) => {
                    sections.push({ type: 'question', content: q, idx });
                  });
                }

                if (sections.length === 0 && normalizedReport.length > 0) {
                  sections.push({ type: 'raw', content: normalizedReport });
                }
                return sections;
              };

              const sections = parseReport(report);
              return sections.map((section, i) => (
                <div key={i} className="flex flex-col gap-4">
                  {section.type === 'student' && (
                    <div>
                      <h3 className="text-xl font-semibold text-indigo-900 mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-indigo-600" />
                        Student Details
                      </h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 bg-indigo-50 p-5 rounded-lg border border-indigo-200 shadow-sm">
                        {Object.entries(section.content as Record<string, string>).map(([label, value]) => (
                          <div key={label} className="flex flex-col">
                            <span className="font-medium text-gray-700 text-sm">{label}:</span>
                            <span className="text-gray-800 text-base whitespace-pre-line break-words">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {section.type === 'header' && (
                    <div>
                      <h3 className="text-xl font-semibold text-indigo-900 mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5 text-indigo-600" />
                        {section.content}
                      </h3>
                      <hr className="border-indigo-200" />
                    </div>
                  )}
                  {section.type === 'question' && (
                    <div>
                      <h4 className="text-lg font-semibold text-indigo-800 mb-4 flex items-center gap-2">
                        {section.content['Question Number'] && section.content['Original Question']
                          ? `${section.content['Question Number']}: ${section.content['Original Question']}`
                          : `Question ${section.idx + 1}`}
                      </h4>
                      <div className="flex flex-col gap-4 bg-gray-50 p-5 rounded-lg border border-gray-200 shadow-sm">
                        {[
                          { label: 'Question Number', icon: '🔢' },
                          { label: 'Original Question', icon: '❓' },
                          { label: 'Mark Range', icon: '📊' },
                          { label: 'Content Validity', icon: '✅' },
                          { label: 'Key Concepts Present', icon: '🔑' },
                          { label: 'Missing or Incorrect Concepts', icon: '❌' },
                          { label: 'Content Sufficiency and Quality', icon: '📝' },
                          { label: 'Mark Justification', icon: '⚖️' },
                          { label: 'Suggestions for Improvement', icon: '💡' },
                        ].map(
                          (f, idx) =>
                            section.content[f.label] && (
                              <div key={f.label} className="flex flex-col">
                                <div className="font-medium text-gray-700 flex items-center gap-2 mb-2 text-sm">
                                  <span>{f.icon}</span>
                                  <span>{f.label}:</span>
                                </div>
                                <div className="bg-white border border-gray-100 rounded-lg px-4 py-3 text-gray-800 text-base shadow-sm">
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content[f.label]}</ReactMarkdown>
                                </div>
                              </div>
                            )
                        )}
                      </div>
                    </div>
                  )}
                  {section.type === 'error' && (
                    <div className="p-4 rounded bg-red-50 border border-red-200 text-red-800 text-sm shadow-sm">
                      <div className="font-semibold mb-2">Error</div>
                      <div>{section.content}</div>
                    </div>
                  )}
                </div>
              ));
            })()}
          </CardContent>
        </Card>
      ))}

      </div>

      {reports.length === 0 && !isGenerating && uploadResponse && (
        <div className="mt-4 p-4 rounded bg-red-50 border border-red-200 text-red-800 text-sm">
          <div className="font-semibold mb-2">No evaluation report available.</div>
          <div>Please ensure the uploaded file is valid and try again.</div>
        </div>
      )}
    </div>
  );
};

export default ReassessmentPdfUpload;