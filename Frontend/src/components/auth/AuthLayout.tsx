import React, { useState, useCallback } from 'react';
import { LoginForm } from './LoginForm';
import { SignupForm } from './SignupForm';
import { ForgotPasswordForm } from './ForgotPasswordForm';
import { ResetPasswordForm } from './ResetPasswordForm';

type AuthView = 'login' | 'signup' | 'forgot' | 'reset';

export const AuthLayout: React.FC = () => {
  const [currentView, setCurrentView] = useState<AuthView>('login');
  const [resetEmail, setResetEmail] = useState('');

  // Use useEffect to track state changes
  React.useEffect(() => {
    console.log('currentView changed to:', currentView);
  }, [currentView]);

  // Memoize navigation callbacks to prevent unnecessary re-renders
  const switchToLogin = useCallback(() => {
    console.log('Switching to login view');
    setCurrentView('login');
  }, []);

  const switchToSignup = useCallback(() => {
    console.log('Switching to signup view');
    setCurrentView('signup');
  }, []);

  const switchToForgot = useCallback(() => {
    console.log('Switching to forgot password view');
    setCurrentView('forgot');
  }, []);

  const switchToReset = useCallback((email: string) => {
    console.log('Switching to reset password view with email:', email);
    setResetEmail(email);
    setCurrentView('reset');
  }, []);

  const renderAuthForm = () => {
    console.log('Rendering auth form with currentView:', currentView);
    
    switch (currentView) {
      case 'login':
        return (
          <LoginForm
            onSwitchToSignup={switchToSignup}
            onSwitchToForgotPassword={switchToForgot}
          />
        );
      case 'signup':
        return (
          <SignupForm
            onSwitchToLogin={switchToLogin}
          />
        );
      case 'forgot':
        return (
          <ForgotPasswordForm
            onSwitchToLogin={switchToLogin}
            onSwitchToReset={switchToReset}
          />
        );
      case 'reset':
        console.log('Rendering ResetPasswordForm with email:', resetEmail);
        return (
          <ResetPasswordForm
            onSwitchToLogin={switchToLogin}
            initialEmail={resetEmail}
          />
        );
      default:
        console.warn('Unknown view:', currentView);
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {renderAuthForm()}
      </div>
      
      {/* Background decorative elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-gradient-primary rounded-full opacity-10 floating-animation"></div>
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-gradient-secondary rounded-full opacity-10 floating-animation" style={{ animationDelay: '2s' }}></div>
        <div className="absolute top-1/2 left-1/4 w-32 h-32 bg-gradient-accent rounded-full opacity-20 floating-animation" style={{ animationDelay: '4s' }}></div>
      </div>
    </div>
  );
};