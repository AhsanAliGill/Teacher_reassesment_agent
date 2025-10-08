import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { AuthLayout } from '@/components/auth/AuthLayout';
import TeacherDashboard from '@/components/dashboard/TeacherDashboard';

const Index = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto bg-gradient-primary rounded-full flex items-center justify-center floating-animation mb-4">
            <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-lg font-medium gradient-text">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <TeacherDashboard /> : <AuthLayout />;
};

export default Index;
