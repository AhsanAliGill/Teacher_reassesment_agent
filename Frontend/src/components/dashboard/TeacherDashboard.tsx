import React, { useState, useEffect } from 'react';
import { Upload, BookOpen, User, LogOut, Plus, GraduationCap } from 'lucide-react';
import { ReassessmentPdfUpload } from './ReassessmentPdfUpload';
import { AssessmentUpload } from './AssessmentUpload';
import { DashboardNavbar } from './DashboardNavbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface Slide {
  id: string;
  name: string;
  subject: string;
  course: string;
  fileName: string;
  uploadDate: string;
  fileSize: string;
}

const TeacherDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const [slides, setSlides] = useState<Slide[]>([
    {
      id: '1',
      name: 'Introduction to Mathematics',
      subject: 'Mathematics',
      course: 'Basic Algebra',
      fileName: 'intro-math.pdf',
      uploadDate: '2024-01-15',
      fileSize: '2.5 MB'
    }
  ]);
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadData, setUploadData] = useState({
    slideName: '',
    subjectName: '',
    courseName: '',
    description: '',
    file: null as File | null
  });
  const [activeTab, setActiveTab] = useState<'slides' | 'reassessment' | 'assessment'>('reassessment');

  useEffect(() => {
    console.log('TeacherDashboard mounted, activeTab:', activeTab);
    setActiveTab('reassessment');
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadData(prev => ({ ...prev, file }));
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uploadData.file) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload.",
        variant: "destructive",
      });
      return;
    }

    if (!uploadData.slideName || !uploadData.subjectName || !uploadData.courseName) {
      toast({
        title: "Missing required fields",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const formData = new FormData();
      formData.append('file', uploadData.file);
      formData.append('slide_name', uploadData.slideName);
      formData.append('subject_name', uploadData.subjectName);
      formData.append('course_name', uploadData.courseName);
      if (uploadData.description) {
        formData.append('description', uploadData.description);
      }

      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/slides/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
          return;
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.[0]?.msg || 'Failed to upload slide');
      }

      const uploadedSlides = await response.json();
      const newSlideData = uploadedSlides[0];

      const newSlide: Slide = {
        id: newSlideData.id,
        name: newSlideData.slide_name,
        subject: newSlideData.subject_name,
        course: newSlideData.course_name,
        fileName: newSlideData.file_name,
        uploadDate: new Date(newSlideData.created_at).toISOString().split('T')[0],
        fileSize: 'N/A'
      };

      setSlides(prev => [newSlide, ...prev]);
      setUploadData({
        slideName: '',
        subjectName: '',
        courseName: '',
        description: '',
        file: null
      });
      setShowUploadForm(false);

      toast({
        title: "Upload successful!",
        description: "Your slide has been uploaded successfully.",
      });
    } catch (error) {
      console.error('Upload failed:', error);
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : 'An error occurred while uploading the slide',
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-background">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-white/20 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center shadow-md">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold gradient-text">Exam Evaluation System</h1>
                <p className="text-sm text-muted-foreground">Teacher Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm font-medium">{user?.name}</span>
              </div>
              <Button
                onClick={logout}
                variant="outline"
                size="sm"
                className="flex items-center space-x-2 hover:bg-destructive hover:text-destructive-foreground transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex">
        <DashboardNavbar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 p-8">
          {/* Welcome Section */}
          <div className="mb-8 fade-in">
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Welcome back, {user?.name}! 👋
            </h2>
            <p className="text-lg text-muted-foreground">
              Manage your teaching materials and upload new slides
            </p>
          </div>

          {/* Assessment Upload Section */}
          {activeTab === 'assessment' && (
            <div className="w-full slide-up">
              <AssessmentUpload />
            </div>
          )}

          {/* Reassessment PDF Upload Section */}
          {activeTab === 'reassessment' && (
            <div className="w-full slide-up">
              <ReassessmentPdfUpload />
            </div>
          )}

          {/* Upload Section */}
          {activeTab === 'slides' && (
            <Card className="glass-card mb-8 slide-up">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl gradient-text">Upload New Slides</CardTitle>
                    <CardDescription className="text-lg">
                      Add new teaching materials to your collection
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setShowUploadForm(!showUploadForm)}
                    className="bg-gradient-primary hover:shadow-glow transition-all duration-300 transform hover:scale-105"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {showUploadForm ? 'Cancel' : 'Upload Slides'}
                  </Button>
                </div>
              </CardHeader>
              {showUploadForm && (
                <CardContent className="p-6">
                  <form onSubmit={handleUpload} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="slideName">Slide Name *</Label>
                        <Input
                          id="slideName"
                          placeholder="Enter slide name"
                          value={uploadData.slideName}
                          onChange={(e) => setUploadData(prev => ({ ...prev, slideName: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="subjectName">Subject *</Label>
                        <Input
                          id="subjectName"
                          placeholder="Enter subject name"
                          value={uploadData.subjectName}
                          onChange={(e) => setUploadData(prev => ({ ...prev, subjectName: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="courseName">Course *</Label>
                        <Input
                          id="courseName"
                          placeholder="Enter course name"
                          value={uploadData.courseName}
                          onChange={(e) => setUploadData(prev => ({ ...prev, courseName: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="file">Slide File *</Label>
                        <Input
                          id="file"
                          type="file"
                          accept=".pdf,.pptx,.ppt"
                          onChange={handleFileChange}
                          className="cursor-pointer"
                          required
                        />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="description">Description (Optional)</Label>
                        <Input
                          id="description"
                          placeholder="Enter a brief description of the slide"
                          value={uploadData.description}
                          onChange={(e) => setUploadData(prev => ({ ...prev, description: e.target.value }))}
                        />
                      </div>
                    </div>
                    <div className="flex justify-end space-x-4 pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setShowUploadForm(false)}
                        disabled={isUploading}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        disabled={isUploading}
                        className="bg-gradient-primary hover:shadow-glow transition-all duration-300 transform hover:scale-105"
                      >
                        {isUploading ? 'Uploading...' : 'Upload Slide'}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              )}
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}

export default TeacherDashboard;