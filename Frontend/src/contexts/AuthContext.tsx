import React, { createContext, useContext, useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'teacher';
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<boolean>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message?: string }>;
  resetPassword: (email: string, pin: string, newPassword: string) => Promise<{ success: boolean; message: string }>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    // Check if user is logged in from localStorage
    const savedUser = localStorage.getItem('teacher_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      // Prepare form data for x-www-form-urlencoded
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      formData.append('grant_type', 'password');
      
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/token', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Login failed:', errorData);
        return false;
      }
      
      const tokenData = await response.json();
      
      // Store the access token
      localStorage.setItem('access_token', tokenData.access_token);
      
      // Create user object with available data
      const user: User = {
        id: '1', // The ID might be in the JWT token, but we'd need to decode it
        email: email,
        name: email.split('@')[0], // Use email prefix as name if not available
        role: tokenData.role || 'teacher' // Default to 'teacher' if role is null
      };
      
      setUser(user);
      localStorage.setItem('teacher_user', JSON.stringify(user));
      
      return true;
    } catch (error) {
      console.error('Error during login:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string): Promise<boolean> => {
    if (isLoading) return false;
    
    setIsLoading(true);
    let signupSuccessful = false;
    
    try {
      // First, try to sign up
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json',
          'Access-Control-Allow-Origin': 'http://localhost:8080'
        },
        body: JSON.stringify({
          email,
          password
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'Signup failed';
        
        // If user already exists, try to log them in instead
        if (errorMessage.includes('already exists') || errorMessage.includes('already registered')) {
          toast({
            title: "Account exists",
            description: "An account with this email already exists. Please log in instead.",
            variant: "default",
          });
          return false;
        }
        
        throw new Error(errorMessage);
      }
      
      // If we get here, signup was successful
      signupSuccessful = true;
      
      // Now try to log the user in automatically
      const loginSuccess = await login(email, password);
      if (!loginSuccess) {
        toast({
          title: "Account created",
          description: "Your account was created successfully. Please log in.",
          variant: "default",
        });
      }
      
      return loginSuccess;
    } catch (error) {
      console.error('Error during signup:', error);
      toast({
        title: "Signup failed",
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        variant: "destructive",
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      // Get the access token from local storage
      const accessToken = localStorage.getItem('access_token');
      
      // Call the backend logout API
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/logout', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to log out from the server');
      }
      
      // Clear local storage and state
      setUser(null);
      localStorage.removeItem('teacher_user');
      localStorage.removeItem('access_token');
      
      toast({
        title: "Logged out",
        description: "You have been successfully logged out.",
        variant: "default",
      });
      
      return true;
    } catch (error) {
      console.error('Error during logout:', error);
      toast({
        title: "Logout failed",
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        variant: "destructive",
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const forgotPassword = async (email: string): Promise<{ success: boolean; message?: string }> => {
    setIsLoading(true);
    
    try {
      console.log('Sending forgot password request for email:', email);
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/forgot-password', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email
        })
      });
      
      console.log('Raw response status:', response.status);
      const data = await response.json().catch(() => ({}));
      console.log('API Response data:', data);
      
      // If the response is not OK, handle the error
      if (!response.ok) {
        console.error('Error response details:', data);
        // Return the error message from the API if available
        return {
          success: false,
          message: data.message || data.detail || 'Failed to send password reset email. Please try again.'
        };
      }
      
      // For successful response (2xx), always return success: true
      // The frontend will handle the navigation to the reset password page
      return {
        success: true,
        message: 'If an account exists with this email, you will receive a password reset PIN.'
      };
    } catch (error) {
      console.error('Error in forgot password:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to process your request'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string, pin: string, newPassword: string): Promise<{ success: boolean; message: string }> => {
    setIsLoading(true);
    
    try {
      console.log('Sending reset password request for email:', email);
      const response = await fetch('https://ahsan462agk-reassesment-agent-backend.hf.space/api/v1/reset-password', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          pin,
          new_password: newPassword
        })
      });
      
      console.log('Reset password response status:', response.status);
      const data = await response.json();
      console.log('Reset password response data:', data);
      
      if (!response.ok) {
        console.error('Error in reset password response:', data);
        return {
          success: false,
          message: data.detail?.[0]?.msg || data.message || 'Failed to reset password. Please try again.'
        };
      }
      
      return {
        success: true,
        message: data.message || 'Your password has been reset successfully.'
      };
    } catch (error) {
      console.error('Error in reset password:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to process your request'
      };
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
    isLoading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};